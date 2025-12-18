from lark import Lark, Transformer, visitors
import sys
import yaml

grammar = r"""
start: (const_decl | dict_block)*

const_decl: "let" NAME "=" value ";"
dict_block: "begin" (assignment ";")+ "end"
assignment: NAME ":=" value

value: NUMBER
      | dict_block
      | const_expr

const_expr: "?" NAME (NUMBER "+" | "min" "(" NUMBER ("," NUMBER)* ")") "?"

NUMBER: /[+-]?([1-9][0-9]*|0)/
NAME: /[a-z][a-z0-9_]*/

SINGLE_COMMENT: /\|\|[^\n]*/
MULTILINE_COMMENT: /\\=begin(?:(?!\\=end).)*\\=end/s

%ignore SINGLE_COMMENT
%ignore MULTILINE_COMMENT
%ignore /\s+/
"""

class T(Transformer):
    def __init__(self):
        self.env = {}
        super().__init__()
    
    def const_decl(self, items):
        name, value = items[0], items[1]
        self.env[name] = value
        return ("const_decl", name, value)
    
    def dict_block(self, items):
        result = {}
        for name, value in items:
            result[name] = value
        return result
    
    def assignment(self, items):
        return (items[0], items[1])
    
    def value(self, items):
        return items[0]
    
    def const_expr(self, items):
        const_name = items[0]
        if const_name not in self.env:
            raise ValueError(f"Константа '{const_name}' не определена")
        
        base_value = self.env[const_name]
      
        if len(items) == 2:  # ?имя 1 +?
            num = items[1]
            return base_value + num
        else:  # ?имя min(1,2,3)?
            numbers = items[1:]
            return min(base_value, *numbers)
    
    def NUMBER(self, token):
        return int(token.value)
    
    NAME = str

def interp(tree, env):
    """Интерпретация AST с учетом окружения (похоже на ваш код)"""
    if isinstance(tree, dict):
        return {k: interp(v, env) for k, v in tree.items()}
    elif isinstance(tree, list):
        # Фильтруем const_decl и собираем словари
        result = []
        for item in tree:
            if isinstance(item, tuple) and item[0] == "const_decl":
                name, value = item[1], item[2]
                env[name] = interp(value, env)
            elif isinstance(item, dict):
                result.append({k: interp(v, env) for k, v in item.items()})
        return result[0] if len(result) == 1 else {"configs": result}
    elif isinstance(tree, (int, str)):
        return tree
    return tree

def main():
    """Чтение из stdin, парсинг, вывод YAML в stdout"""
    # Чтение из стандартного ввода
    input_text = sys.stdin.read()
    
    if not input_text.strip():
        print("Ошибка: пустой ввод", file=sys.stderr)
        sys.exit(1)
    
 
    try:
        parser = Lark(grammar, parser='lalr')
        tree = parser.parse(input_text)
    except Exception as e:
        print(f"Синтаксическая ошибка: {e}", file=sys.stderr)
        sys.exit(1)
    
    
    try:
        transformer = T()
        transformed_tree = transformer.transform(tree)
        
        env = {}
        result = interp(transformed_tree, env)
        

        yaml.dump(result, sys.stdout, 
                  allow_unicode=True, 
                  default_flow_style=False, 
                  sort_keys=False)
    except ValueError as e:
        print(f"Семантическая ошибка: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Ошибка преобразования: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
