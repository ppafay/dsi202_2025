# dsi202/outfits/forms.py

from django import forms
from django.core.exceptions import ValidationError
from .models import Outfit, CartItem, Cart
from datetime import date, timedelta

class OutfitForm(forms.ModelForm):
    class Meta:
        model = Outfit
        fields = ['name', 'description', 'price', 'image']

class CartItemDateSelectionForm(forms.ModelForm):
    start_date = forms.DateField(
        label="วันที่เริ่มเช่า",
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control form-control-sm datepicker'}),
        required=True
    )
    end_date = forms.DateField(
        label="วันที่ส่งคืน",
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control form-control-sm datepicker'}),
        required=True
    )

    class Meta:
        model = CartItem
        fields = ['start_date', 'end_date']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set initial values only if the form is not bound and instance doesn't have values
        if not (self.is_bound or (self.instance and self.instance.pk)):
            if not self.initial.get('start_date') and (not self.instance or not self.instance.start_date):
                self.initial['start_date'] = date.today()
            if not self.initial.get('end_date') and (not self.instance or not self.instance.end_date):
                self.initial['end_date'] = date.today() + timedelta(days=2) # e.g., 3-day rental

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get("start_date")
        end_date = cleaned_data.get("end_date")

        if start_date and end_date:
            if start_date < date.today():
                self.add_error('start_date', "วันที่เริ่มเช่าต้องไม่ใช่วันที่ผ่านมาแล้ว")
            if end_date < start_date:
                self.add_error('end_date', "วันที่ส่งคืนต้องไม่มาก่อนวันที่เริ่มเช่า")
            # Minimum 1-day rental (e.g., start today, end today)
            if (end_date - start_date).days < 0:
                 self.add_error('end_date', "ระยะเวลาการเช่าไม่ถูกต้อง")
        return cleaned_data

class PaymentConfirmationForm(forms.Form):
    slip = forms.ImageField(label="อัปโหลดสลิปการโอน", required=True, widget=forms.ClearableFileInput(attrs={'class': 'form-control'}))

class CustomerOrderImageUploadForm(forms.ModelForm):
    class Meta:
        model = Cart
        fields = ['customer_uploaded_image']
        widgets = {
            'customer_uploaded_image': forms.ClearableFileInput(attrs={'class': 'form-control form-control-sm'}),
        }
        labels = {
            'customer_uploaded_image': 'แนบรูปภาพประกอบปัญหา (ถ้ามี):'
        }

class ReturnShipmentForm(forms.ModelForm):
    return_tracking_number = forms.CharField(
        label="เลขพัสดุสำหรับส่งคืน",
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control form-control-sm', 'placeholder': 'เช่น TH123456789EX'})
    )
    return_shipment_image = forms.ImageField(
        label="แนบรูปภาพหลักฐานการส่ง (เช่น สลิปขนส่ง)",
        required=True, # Consider making this optional if not always available
        widget=forms.ClearableFileInput(attrs={'class': 'form-control form-control-sm'})
    )

    class Meta:
        model = Cart
        fields = ['return_tracking_number', 'return_shipment_image']