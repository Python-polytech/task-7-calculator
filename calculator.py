import math
import re
import logging

class CalculatorError(Exception):
    """Базовая ошибка калькулятора."""
    pass

class TokenizeError(CalculatorError):
    """Не удалось разобрать строку на токены."""
    pass

class ParenthesisError(CalculatorError):
    """Несбалансированные скобки."""
    pass

class ParseError(CalculatorError):
    """Синтаксическая ошибка выражения."""
    pass

class Calculator:
    PRIORITY = {
        '+': 1, '-': 1,
        '*': 2, '/': 2,
        '^': 3,
    }
    RIGHT_ASSOC = {'^'}

    TOKEN_PATTERN = re.compile(
        r'(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?|inf|nan|[+\-*/^()]|_',
        re.IGNORECASE,
    )

    def __init__(self):
        self._previous_result = None
        self.logger = logging.getLogger(self.__class__.__name__)

    def _tokenize(self, expression: str) -> list[str]:
        """Разбивает входное выражение на отдельные токены."""
        tokens = []
        pos = 0
        n = len(expression)

        while pos < n:
            if expression[pos].isspace():
                pos += 1
                continue
            match = self.TOKEN_PATTERN.match(expression, pos)
            if not match:
                raise TokenizeError(
                    f"Неизвестный символ {expression[pos]!r} на позиции {pos}"
                )
            token = match.group(0)
            if token.lower() in ('inf', 'nan'):
                token = token.lower()
            tokens.append(token)
            pos = match.end()

        self.logger.debug("Токенизация: %r -> %s", expression, tokens)
        return tokens

    def _check_parentheses(self, tokens: list[str]) -> None:
        """Проверяет правильность расстановки скобок."""
        depth = 0
        for token in tokens:
            if token == '(':
                depth += 1
            elif token == ')':
                depth -= 1
                if depth < 0:
                    raise ParenthesisError("Лишняя закрывающая скобка")
        if depth > 0:
            raise ParenthesisError("Незакрытая открывающая скобка")

    def _parse_unary(self, tokens: list[str]) -> float:
        """Обрабатывает последовательность унарных знаков."""
        sign = 1.0

        while tokens and tokens[0] in ('+', '-'):
            if tokens[0] == '-':
                sign *= -1.0
            tokens = tokens[1:]
        return sign * self._parse(tokens)

    def _parse_signed_power(self, tokens: list[str], power_idx: int) -> float:
        """Обрабатывает унарный знак перед основанием степени."""
        sign = 1.0
        sign_end = 0

        while sign_end < power_idx and tokens[sign_end] in ('+', '-'):
            if tokens[sign_end] == '-':
                sign *= -1.0
            sign_end += 1

        if sign_end == power_idx:
            raise ParseError("Отсутствует основание степени")

        base = self._parse(tokens[sign_end:power_idx])
        exponent = self._parse(tokens[power_idx + 1:])

        return sign * self._apply_operator('^', base, exponent)

    def _parse(self, tokens: list[str]) -> float:
        """Рекурсивно разбирает и вычисляет арифметическое выражение."""
        if not tokens:
            raise ParseError("Пустое выражение")

        if tokens[0] == '(' and self._matching_bracket(tokens, 0) == len(tokens) - 1:
            return self._parse(tokens[1:-1])

        idx = self._find_main_operator(tokens)

        if idx is None:
            if tokens[0] in ('+', '-'):
                return self._parse_unary(tokens)
            return self._parse_atom(tokens)

        operator = tokens[idx]
        left_tokens = tokens[:idx]
        right_tokens = tokens[idx + 1:]

        if not left_tokens or not right_tokens:
            raise ParseError(f"Оператор {operator} без операнда")

        if tokens[0] in ('+', '-') and operator == '^':
            return self._parse_signed_power(tokens, idx)

        left = self._parse(left_tokens)
        right = self._parse(right_tokens)

        return self._apply_operator(operator, left, right)

    def _matching_bracket(self, tokens: list[str], open_idx: int) -> int:
        """Находит закрывающую скобку для заданной открывающей."""
        depth = 0
        for i in range(open_idx, len(tokens)):
            if tokens[i] == '(':
                depth += 1
            elif tokens[i] == ')':
                depth -= 1
                if depth == 0:
                    return i
        raise ParenthesisError("Не найдена парная скобка")

    def _find_main_operator(self, tokens: list[str]) -> int | None:
        """Находит главный оператор с учётом приоритетов и ассоциативности."""
        depth = 0
        best_idx = None
        best_priority = None

        for i, token in enumerate(tokens):
            if token == '(':
                depth += 1
                continue
            if token == ')':
                depth -= 1
                continue
            if depth != 0 or token not in self.PRIORITY:
                continue

            if self._is_unary(tokens, i):
                continue

            priority = self.PRIORITY[token]
            if best_priority is None or priority < best_priority:
                best_idx, best_priority = i, priority
            elif priority == best_priority:
                if token not in self.RIGHT_ASSOC:
                    best_idx = i
        return best_idx

    def _is_unary(self, tokens: list[str], idx: int) -> bool:
        """Определяет, является ли знак унарным оператором."""
        if tokens[idx] not in ('+', '-'):
            return False
        if idx == 0:
            return True
        prev = tokens[idx - 1]
        return prev in self.PRIORITY or prev == '('

    def _parse_atom(self, tokens: list[str]) -> float:
        """Преобразует отдельный токен в число или предыдущий результат."""
        if len(tokens) != 1:
            raise ParseError(f"Ожидалось число или _, получено: {tokens}")
        token = tokens[0]

        if token == '_':
            if self._previous_result is None:
                raise ParseError("Предыдущий результат ещё не определён")
            return self._previous_result
        if token.lower() == 'inf':
            return math.inf
        if token.lower() == 'nan':
            return math.nan
        try:
            return float(token)
        except ValueError:
            raise ParseError(f"Не число: {token!r}")

    def _apply_operator(self, op: str, left: float, right: float) -> float:
        """Выполняет арифметическую операцию над двумя числами."""
        self.logger.debug("Применение: %s %s %s", left, op, right)

        if op == '+':
            return left + right
        if op == '-':
            return left - right
        if op == '*':
            return left * right
        if op == '/':
            if right == 0.0:
                if left == 0.0 or math.isnan(left):
                    return math.nan
                sign = math.copysign(1.0, left) * math.copysign(1.0, right)
                return math.copysign(math.inf, sign)
            return left / right
        if op == '^':
            return self._power(left, right)
        raise ParseError(f"Неизвестный оператор: {op!r}")

    def _power(self, base: float, exp: float) -> float:
        """Вычисляет степень с обработкой особых случаев."""
        if base == 0.0 and exp < 0:
            sign = 1.0

            if math.copysign(1.0, base) < 0:
                if math.isfinite(exp) and exp.is_integer():
                    if int(exp) % 2 != 0:
                        sign = -1.0
            return math.copysign(math.inf, sign)
        try:
            return math.pow(base, exp)
        except OverflowError:
            if base < 0 and math.isfinite(exp) and exp.is_integer():
                if int(exp) % 2 != 0:
                    return -math.inf
            return math.inf
        except ValueError:
            return math.nan

    def calculate(self, expression: str) -> float:
        """Вычисляет выражение и сохраняет полученный результат."""
        self.logger.info("Вычисление: %r", expression)
        tokens = self._tokenize(expression)
        self._check_parentheses(tokens)
        result = self._parse(tokens)
        self._previous_result = result
        self.logger.info("Результат: %s", result)
        return result
