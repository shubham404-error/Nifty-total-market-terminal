import re
with open("engine.py", "r", encoding="utf-8") as f:
    code = f.read()

# Extract convergence_table source
match = re.search(r'(def convergence_table\(.*?)(?=def investor_quality_gate)', code, re.DOTALL)
if match:
    func_code = match.group(1)
    
    # Rename
    func_code_v2 = func_code.replace("def convergence_table(", "def convergence_table_v2(")
    
    # Remove RSI from Momentum
    func_code_v2 = func_code_v2.replace("+ (rsi >= 50).astype(int) * 5", "")
    
    # Redistribute points: rs3 10 -> 15 in FreshMomentumScore
    func_code_v2 = func_code_v2.replace("+ (rs3 >= 70).astype(int) * 10\n        \n", "+ (rs3 >= 70).astype(int) * 15\n")
    
    # Let's use regex to redistribute 5 points to rs3 in FreshMomentum
    # It's easier to just do string replacement
    func_v2_lines = func_code_v2.split('\n')
    
    in_momentum = False
    in_breakout = False
    out_lines = []
    
    for line in func_v2_lines:
        if "fresh_momentum_score = (" in line:
            in_momentum = True
        elif "breakout_score = (" in line:
            in_breakout = True
        
        if in_momentum and "+ (rs3 >= 70).astype(int) * 10" in line:
            line = line.replace("10", "15")
        
        if in_breakout and "+ (rs3 >= 70).astype(int) * 15" in line:
            line = line.replace("15", "20")
            
        if "df[\"FreshMomentumScore\"] = 0" in line:
            in_momentum = False
        if "df[\"BreakoutScore\"] = 0" in line:
            in_breakout = False
            
        out_lines.append(line)
        
    func_code_v2 = '\n'.join(out_lines)
    
    code = code.replace(func_code, func_code + "\n" + func_code_v2)
    
    with open("engine.py", "w", encoding="utf-8") as f:
        f.write(code)
    print("Added convergence_table_v2 to engine.py")
else:
    print("Could not find convergence_table")
