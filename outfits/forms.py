# dsi202/outfits/forms.py

from django import forms
from django.core.exceptions import ValidationError
from .models import Outfit, CartItem, Cart # <<< IMPORT Cart
from datetime import date, timedelta

class OutfitForm(forms.ModelForm):
    class Meta:
        model = Outfit
        fields = ['name', 'description', 'price', 'image']

class CartItemDateSelectionForm(forms.ModelForm):
    start_date = forms.DateField(
        label="วันที่เริ่มเช่า",
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control form-control-sm'}),
        required=True
    )
    end_date = forms.DateField(
        label="วันที่ส่งคืน",
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control form-control-sm'}),
        required=True
    )

    class Meta:
        model = CartItem
        fields = ['start_date', 'end_date']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance or not self.instance.start_date:
            self.fields['start_date'].initial = date.today()
        if not self.instance or not self.instance.end_date:
            self.fields['end_date'].initial = date.today() + timedelta(days=1)

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get("start_date")
        end_date = cleaned_data.get("end_date")

        if start_date and end_date:
            if start_date < date.today():
                self.add_error('start_date', "วันที่เริ่มเช่าต้องไม่ใช่วันที่ผ่านมาแล้ว")
            if end_date < start_date:
                self.add_error('end_date', "วันที่ส่งคืนต้องไม่มาก่อนวันที่เริ่มเช่า")
        return cleaned_data

class PaymentConfirmationForm(forms.Form):
    slip = forms.ImageField(label="อัปโหลดสลิปการโอน", required=True)

class CustomerOrderImageUploadForm(forms.ModelForm):
    class Meta:
        model = Cart
        fields = ['customer_uploaded_image']
        widgets = {
            'customer_uploaded_image': forms.FileInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'customer_uploaded_image': 'แนบรูปภาพ (ถ้ามีปัญหาเกี่ยวกับสินค้า):'
        }