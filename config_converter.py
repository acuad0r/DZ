#!/usr/bin/env python3
import sys
import re
import yaml

class ConfigParser:
    def __init__(self):
        self.constants = {}
        self.result = {}
    
    def parse(self, input_text: str) -> dict:
        cleaned_text = self._remove_comments(input_text)
        cleaned_text = self._parse_constants(cleaned_text)
        self.result = self._parse_dictionaries(cleaned_text)
        self._replace_constants_in_result()
        return self.result
    
    def _remove_comments(self, text: str) -> str:
        lines = []
        in_multiline_comment = False
        
        for line in text.split('\n'):
            if '=begin' in line:
                in_multiline_comment = True
                continue
            if '=end' in line:
                in_multiline_comment = False
                continue
            
            if not in_multiline_comment:
                if '||' in line:
                    line = line.split('||')[0]
                lines.append(line)
        
        return '\n'.join(lines)
    
    def _parse_constants(self, text: str) -> str:
        lines = text.split('\n')
        result_lines = []
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            if line.startswith('let '):
                const_expr = line
                j = i + 1
                while j < len(lines) and ';' not in const_expr:
                    const_expr += ' ' + lines[j].strip()
                    j += 1
                
                match = re.match(r'let\s+([a-z][a-z0-9_]*)\s*=\s*(.+);', const_expr, re.DOTALL)
                if match:
                    name = match.group(1)
                    value_expr = match.group(2).strip()
                    value = self._evaluate_constant_expression(value_expr)
                    self.constants[name] = value
                
                i = j
            else:
                result_lines.append(lines[i])
                i += 1
        
        return '\n'.join(result_lines)
    
    def _evaluate_constant_expression(self, expr: str) -> int:
        expr = expr.strip()
        
        if re.match(r'^[+-]?([1-9][0-9]*|0)$', expr):
            return int(expr)
        
        if expr in self.constants:
            return self.constants[expr]
        
        # Разбиваем на токены, учитывая функции с аргументами
        tokens = []
        i = 0
        while i < len(expr):
            if expr[i] == ' ':
                i += 1
                continue
            
            # Если встретили min(
            if expr[i:i+4] == 'min(':
                # Ищем закрывающую скобку
                paren_count = 1
                j = i + 4
                while j < len(expr) and paren_count > 0:
                    if expr[j] == '(':
                        paren_count += 1
                    elif expr[j] == ')':
                        paren_count -= 1
                    j += 1
                tokens.append(expr[i:j])
                i = j
            else:
                # Обычный токен
                j = i
                while j < len(expr) and expr[j] != ' ':
                    j += 1
                tokens.append(expr[i:j])
                i = j
        
        stack = []
        
        for token in tokens:
            if re.match(r'^[+-]?([1-9][0-9]*|0)$', token):
                stack.append(int(token))
            elif token in self.constants:
                stack.append(self.constants[token])
            elif token == '+':
                if len(stack) < 2:
                    raise ValueError(f"Недостаточно операндов для операции +")
                b = stack.pop()
                a = stack.pop()
                stack.append(a + b)
            elif token.startswith('min(') and token.endswith(')'):
                # Извлекаем аргументы из min(100, 50)
                args_str = token[4:-1]
                args = []
                for arg in args_str.split(','):
                    arg = arg.strip()
                    if arg in self.constants:
                        args.append(self.constants[arg])
                    else:
                        args.append(int(arg))
                if args:
                    stack.append(min(args))
                else:
                    raise ValueError(f"Функция min без аргументов")
            else:
                raise ValueError(f"Неизвестный токен: {token}")
        
        if len(stack) != 1:
            raise ValueError(f"Некорректное выражение")
        
        return stack[0]
    
    def _parse_dictionaries(self, text: str) -> dict:
        result = {}
        
        # Удаляем комментарии и лишние пробелы
        text = text.strip()
        if not text:
            return result
        
        # Ищем begin...end
        pattern = r'begin(.*?)end'
        matches = re.findall(pattern, text, re.DOTALL)
        
        for dict_content in matches:
            # Разбиваем на строки и убираем пустые
            lines = [line.strip() for line in dict_content.split('\n') if line.strip()]
            
            for line in lines:
                # Парсим поле вида "name := value;"
                if ':=' in line and line.endswith(';'):
                    name, value_part = line.split(':=', 1)
                    name = name.strip()
                    value_str = value_part[:-1].strip()  # Убираем ;
                    
                    if re.match(r'^[+-]?([1-9][0-9]*|0)$', value_str):
                        result[name] = int(value_str)
                    elif value_str.startswith('begin'):
                        nested_dict = self._parse_dictionaries(value_str)
                        if nested_dict:
                            result[name] = nested_dict
                    elif '^(' in value_str:
                        expr_match = re.match(r'\^\((.+)\)', value_str)
                        if expr_match:
                            expr = expr_match.group(1)
                            result[name] = self._evaluate_constant_expression(expr)
                    else:
                        # Убираем лишние кавычки
                        if value_str.startswith('"') and value_str.endswith('"'):
                            value_str = value_str[1:-1]
                        elif value_str.startswith("'") and value_str.endswith("'"):
                            value_str = value_str[1:-1]
                        result[name] = value_str
        
        return result
    
    def _replace_constants_in_result(self):
        def replace_in_dict(d):
            for key, value in list(d.items()):
                if isinstance(value, dict):
                    replace_in_dict(value)
                elif isinstance(value, str) and value in self.constants:
                    d[key] = self.constants[value]
        
        replace_in_dict(self.result)

def main():
    try:
        input_text = sys.stdin.read()
        
        parser = ConfigParser()
        result = parser.parse(input_text)
        
        yaml_output = yaml.dump(
            result, 
            default_flow_style=False, 
            allow_unicode=True, 
            indent=2,
            sort_keys=False
        )
        
        sys.stdout.write(yaml_output)
        
    except Exception as e:
        sys.stderr.write(f"Ошибка: {e}\n")
        sys.exit(1)

if __name__ == "__main__":
    main()
