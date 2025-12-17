```markdown
# Конвертер конфигураций

Программа преобразует учебный конфигурационный язык в YAML.

## Установка
```bash
pip install pyyaml
```

## Использование
```bash
python config_converter.py < input.txt
```

## Пример

### Входной файл `input.txt`
```
let base = 10;
let offset = 5;

begin
    server := begin
        port := ^(base offset +);
        host := "localhost";
    end;
    
    limits := begin
        timeout := 30;
        max_conn := ^(min(100, 50));
    end;
end
```

### Запуск
```bash
python config_converter.py < input.txt
```

### Выход программы
```yaml
server:
  port: 15
  host: localhost
limits:
  timeout: 30
  max_conn: 50
```

## Язык конфигурации

### Комментарии
- `|| Однострочный`
- ```
  =begin
  Многострочный
  =end
  ```

### Числа
- Формат: `123`, `0`, `-42`
- Нельзя: `0123`, `1.5`

### Имена
- `server`, `port_80`, `max_conn`
- Нельзя: `Server`, `1port`

### Константы
```python
let timeout = 30;
let count = ^(10 20 +);
```

### Словари
```python
begin
    name := "value";
    number := 42;
end
```

### Выражения
- `^(10 20 +)` → 30
- `^(min(5, 10, 3))` → 3

## Требования
- Python 3.6+
- PyYAML
```
