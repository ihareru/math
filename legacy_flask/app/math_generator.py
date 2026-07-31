import random


def generate_example(mode):
    if mode == "add":
        title = "на сложение"
        operation = "+"
    elif mode == "sub":
        title = "на вычетание"
        operation = "-"
    elif mode == "mul":
        title = "на умножение"
        operation = "*"
    elif mode == "div":
        title = "на деление"
        operation = "/"
    else:
        title = "в случайном порядке"
        operation = random.choice(["+", "-", "*", "/"])

    if operation == "+":
        while True:
            num1 = random.randint(1, 100)
            num2 = random.randint(1, 100)
            answer = num1 + num2
            if answer <= 100:
                break

    elif operation == "-":
        num1 = random.randint(1, 100)
        num2 = random.randint(1, num1)
        answer = num1 - num2

    elif operation == "*":
        num1 = random.randint(1, 10)
        num2 = random.randint(1, 10)
        answer = num1 * num2

    else:
        num2 = random.randint(1, 10)
        answer = random.randint(1, 10)
        num1 = num2 * answer

    return {
        "title": title,
        "num1": num1,
        "num2": num2,
        "operation": ":" if operation == "/" else operation,
        "answer": answer
    }
