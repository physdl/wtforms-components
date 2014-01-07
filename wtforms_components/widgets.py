from cgi import escape
from copy import copy
import six
from wtforms.widgets import (
    HTMLString,
    html_params
)
from wtforms.compat import text_type
from wtforms.validators import NumberRange, DataRequired
from wtforms.widgets import Input
from .validators import DateRange, TimeRange


def min_max(field, validator_class):
    """
    Returns maximum minimum and minimum maximum value for given validator class
    of given field.

    :param field: WTForms Field object
    :param validator_class: WTForms Validator class

    Example::


        class MyForm(Form):
            some_integer_field = IntegerField(
                validators=[Length(min=3, max=6), Length(min=4, max=7)]
            )

        form = MyForm()

        min_max(form.some_integer_field, Length)
        # {'min': 4, 'max': 6}
    """
    min_values = []
    max_values = []
    for validator in field.validators:
        if isinstance(validator, validator_class):
            if validator.min is not None:
                min_values.append(validator.min)
            if validator.max is not None:
                max_values.append(validator.max)

    data = {}
    if min_values:
        data['min'] = max(min_values)
    if max_values:
        data['max'] = min(max_values)
    return data


def has_validator(field, validator_class):
    """
    Returns whether or not given field has an instance of given validator class
    in the validators property.

    :param field: WTForms Field object
    :param validator_class: WTForms Validator class
    """
    return any([
        isinstance(validator, validator_class)
        for validator in field.validators
    ])


class HTML5Input(Input):
    def __init__(self, **kwargs):
        self.options = kwargs

    def __call__(self, field, **kwargs):
        if has_validator(field, DataRequired):
            kwargs.setdefault('required', True)

        for key, value in self.range_validators(field).items():
            kwargs.setdefault(key, value)

        if hasattr(field, 'widget_options'):
            for key, value in self.field.widget_options:
                kwargs.setdefault(key, value)

        options_copy = copy(self.options)
        options_copy.update(kwargs)
        return super(HTML5Input, self).__call__(field, **options_copy)

    def range_validators(self, field):
        return {}


class BaseDateTimeInput(HTML5Input):
    """
    Base class for TimeInput, DateTimeLocalInput, DateTimeInput and
    DateInput widgets
    """
    range_validator_class = DateRange

    def range_validators(self, field):
        data = min_max(field, self.range_validator_class)
        if 'min' in data:
            data['min'] = data['min'].strftime(self.format)
        if 'max' in data:
            data['max'] = data['max'].strftime(self.format)
        return data


class TextInput(HTML5Input):
    input_type = 'text'


class SearchInput(HTML5Input):
    """
    Renders an input with type "search".
    """
    input_type = 'search'


class MonthInput(HTML5Input):
    """
    Renders an input with type "month".
    """
    input_type = 'month'


class WeekInput(HTML5Input):
    """
    Renders an input with type "week".
    """
    input_type = 'week'


class RangeInput(HTML5Input):
    """
    Renders an input with type "range".
    """
    input_type = 'range'


class URLInput(HTML5Input):
    """
    Renders an input with type "url".
    """
    input_type = 'url'


class ColorInput(HTML5Input):
    """
    Renders an input with type "tel".
    """
    input_type = 'color'


class TelInput(HTML5Input):
    """
    Renders an input with type "tel".
    """
    input_type = 'tel'


class EmailInput(HTML5Input):
    """
    Renders an input with type "email".
    """
    input_type = 'email'


class TimeInput(BaseDateTimeInput):
    """
    Renders an input with type "time".

    Adds min and max html5 field parameters based on field's TimeRange
    validator.
    """
    input_type = 'time'
    range_validator_class = TimeRange
    format = '%H:%M:%S'


class DateTimeLocalInput(BaseDateTimeInput):
    """
    Renders an input with type "datetime-local".

    Adds min and max html5 field parameters based on field's DateRange
    validator.
    """
    input_type = 'datetime-local'
    format = '%Y-%m-%dT%H:%M:%S'


class DateTimeInput(BaseDateTimeInput):
    """
    Renders an input with type "datetime".

    Adds min and max html5 field parameters based on field's DateRange
    validator.
    """
    input_type = 'datetime'
    format = '%Y-%m-%dT%H:%M:%SZ'


class DateInput(BaseDateTimeInput):
    """
    Renders an input with type "date".

    Adds min and max html5 field parameters based on field's DateRange
    validator.
    """
    input_type = 'date'
    format = '%Y-%m-%d'


class NumberInput(HTML5Input):
    """
    Renders an input with type "number".

    Adds min and max html5 field parameters based on field's NumberRange
    validator.
    """
    input_type = 'number'
    range_validator_class = NumberRange

    def range_validators(self, field):
        return min_max(field, self.range_validator_class)


class ReadOnlyWidgetProxy(object):
    def __init__(self, widget):
        self.widget = widget

    def __getattr__(self, name):
        return getattr(self.widget, name)

    def __call__(self, field, **kwargs):
        kwargs.setdefault('readonly', True)
        return self.widget(field, **kwargs)


class SelectWidget(object):
    """
    Add support of choices with ``optgroup`` to the ``Select`` widget.
    """
    def __init__(self, multiple=False):
        self.multiple = multiple

    def __call__(self, field, **kwargs):
        kwargs.setdefault('id', field.id)
        if self.multiple:
            kwargs['multiple'] = True
        html = ['<select %s>' % html_params(name=field.name, **kwargs)]
        html.extend(
            self.render_choice(field, choice)
            for choice in field.iter_choices()
        )
        html.append('</select>')
        return HTMLString(''.join(html))

    @classmethod
    def render_choice(cls, field, choice):
        from wtforms_components.fields.select import Choice, Choices

        if isinstance(choice, Choices):
            return cls.render_optgroup(field, choice)
        elif isinstance(choice, Choice):
            if isinstance(field.data, list):
                selected = choice.value in field.data
            else:
                selected = field.data == choice.value

            return cls.render_option(
                choice.key,
                choice.label,
                selected
            )

    @classmethod
    def render_optgroup(cls, field, choices):
        html = u'<optgroup label="%s">%s</optgroup>'
        data = (escape(six.text_type(choices.label)), u'\n'.join(
            cls.render_choice(field, choice) for choice in choices
        ))
        return HTMLString(html % data)

    @classmethod
    def render_option(cls, value, label, selected, **kwargs):
        if value is True:
            # Handle the special case of a 'True' value.
            value = text_type(value)

        options = dict(kwargs, value=value)
        if selected:
            options['selected'] = True
        return HTMLString('<option %s>%s</option>' % (
            html_params(**options), escape(six.text_type(label)))
        )

