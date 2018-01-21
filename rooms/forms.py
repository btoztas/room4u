from django import forms


class MessageForm(forms.Form):
    subject = forms.CharField(label='subject', max_length=100)
    message = forms.CharField(label='message', max_length=1000)
    destination = forms.CharField(label='destination', max_length=1000)
    destflag = forms.CharField(label='destflag', max_length=1000)

class FilterForm(forms.Form):
    filter = forms.CharField(label='filter', max_length=100)
    text = forms.CharField(label='text', max_length=100)
    date = forms.CharField(label='date', max_length=100)
    sdate = forms.CharField(label='sdate', max_length=100)


class SearchRoomForm(forms.Form):
    keyword = forms.CharField(label='keyword', max_length=100)


class AdminSearchForm(forms.Form):
    search_keyword = forms.CharField(label='keyword', max_length=100)
    search_type = forms.CharField(label='type', max_length=100)
