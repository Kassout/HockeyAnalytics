import message_properties as msg


def build_message(*messages):
    builded_message = ''
    for message in messages:
        builded_message += message + '\n'
    return builded_message


def find_dictvalue_in_list(lst, key, value):
    for i, dic in enumerate(lst):
        if dic[key] == value:
            return i
    return -1


def input_int_recall(message, input_message = 'Input: '):
    input_value = input(message + '\n' + input_message)
    while True:
        try:
            return int(input_value)
        except ValueError:
            # Not a valid number
            print('\n' + msg.message_error_number_format)
            input_value = input(message + '\n' + input_message)

