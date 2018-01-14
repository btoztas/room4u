from django import forms

class MessageForm(forms.Form):
    rname = forms.CharField(label='rname', max_length=100)
    subject = forms.CharField(label='subject', max_length=100)
    message = forms.CharField(label='message', max_length=1000)

class FilterForm(forms.Form):
    filter = forms.CharField(label='filter', max_length=100)
    text = forms.CharField(label='text', max_length=100)
    date = forms.CharField(label='date', max_length=100)
    sdate = forms.CharField(label='sdate', max_length=100)