from allauth.account.forms import LoginForm as AllAuthLoginForm
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit

class CustomLoginForm(AllAuthLoginForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_class = 'login'
        self.helper.form_method = 'post'
        self.helper.form_tag = True
        self.helper.layout = Layout(
            'login',
            'password',
            'remember',
            Submit('submit', 'Sign In', css_class='btn btn-primary w-100')
        )
