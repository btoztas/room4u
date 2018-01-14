from django import forms


class MessageForm(forms.Form):
    rname = forms.CharField(label='rname', max_length=100)
    subject = forms.CharField(label='subject', max_length=100)
    message = forms.CharField(label='message', max_length=1000)


class SearchRoomFrom(forms.Form):
    keyword = forms.CharField(label='rname', max_length=100)