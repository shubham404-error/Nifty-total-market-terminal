import re
code = open('app.py', encoding='utf-8').read()
code = code.replace('"EV/EBITDA"', '"EV/EBITDA", "ROE %"')
open('app.py', 'w', encoding='utf-8').write(code)
