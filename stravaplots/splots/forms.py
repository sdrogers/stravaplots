from django import forms

class TokenForm(forms.Form):
	n_recent = forms.IntegerField(required = True,initial = 20)
	from_date = forms.DateField(required = True,widget=forms.SelectDateWidget(years = range(2015,2020)))