import logging
from calculator import Calculator, CalculatorError
from logger_setup import setup_logging

def print_menu():
    print("=" * 50)
    print("             ВЕЩЕСТВЕННЫЙ КАЛЬКУЛЯТОР")
    print("=" * 50)
    print("Поддерживаемые операции:")
    print("  +  сложение")
    print("  -  вычитание")
    print("  *  умножение")
    print("  /  деление")
    print("  ^  возведение в степень")
    print()
    print("Дополнительные возможности:")
    print("  ()     скобки")
    print("  -      унарный минус")
    print("  _      предыдущий результат")
    print("  inf    положительная бесконечность")
    print("  -inf   отрицательная бесконечность")
    print("  nan    неопределённое значение")
    print()
    print("Для вывода справки введите help или h.")
    print("Для выхода введите exit, quit или q.")
    print("Пример: (2 + 3) * 4^2")
    print("=" * 50)

def main() -> int:
    setup_logging()
    logger = logging.getLogger("main")

    calc = Calculator()
    logger.info("Калькулятор запущен")
    print_menu()

    while True:
        try:
            expression = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            logger.info("Работа прервана пользователем")
            print()
            break

        if expression.lower() in ('quit', 'exit', 'q'):
            logger.info("Калькулятор завершил работу")
            break
        if expression.lower() in ('help', 'h'):
            print_menu()
            continue
        if not expression:
            continue

        try:
            result = calc.calculate(expression)
            print(result)
        except CalculatorError as e:
            logger.warning("Ошибка в выражении %r: %s", expression, e)
            print(f"Ошибка: {e}")
        except Exception as e:
            logger.exception("Неожиданная ошибка")
            print(f"Внутренняя ошибка: {e}")
    return 0


if __name__ == "__main__":
    main()