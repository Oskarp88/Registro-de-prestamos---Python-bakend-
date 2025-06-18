from babel.numbers import format_currency

def format_currency_value(value):
    return format_currency(value, 'COP', locale='es_CO')
