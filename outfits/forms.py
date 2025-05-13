# dsi202/outfits/forms.py

from django import forms
from django.core.exceptions import ValidationError
from .models import Outfit, CartItem, Cart, Category
from datetime import date, timedelta
from django.utils.safestring import mark_safe

class OutfitForm(forms.ModelForm):
    category = forms.ModelChoiceField(
        queryset=Category.objects.all(),
        empty_label="เลือกหมวดหมู่...",
        required=False,
        widget=forms.Select(attrs={'class': 'form-select form-control'})
    )
    class Meta:
        model = Outfit
        fields = ['name', 'category', 'description', 'price', 'image']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'price': forms.NumberInput(attrs={'class': 'form-control'}),
            'image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }

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
        if not (self.is_bound or (self.instance and self.instance.pk and self.instance.start_date)):
            self.initial['start_date'] = date.today()
        if not (self.is_bound or (self.instance and self.instance.pk and self.instance.end_date)):
            self.initial['end_date'] = date.today() + timedelta(days=2)

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get("start_date")
        end_date = cleaned_data.get("end_date")
        outfit_to_check = self.instance.outfit if self.instance and hasattr(self.instance, 'outfit') and self.instance.outfit_id else None

        if start_date and end_date:
            if start_date < date.today():
                self.add_error('start_date', "วันที่เริ่มเช่าต้องไม่ใช่วันที่ผ่านมาแล้ว")
            if end_date < start_date:
                self.add_error('end_date', "วันที่ส่งคืนต้องไม่มาก่อนวันที่เริ่มเช่า")
            if (end_date - start_date).days < 0 :
                 self.add_error('end_date', "ระยะเวลาการเช่าไม่ถูกต้อง (อย่างน้อย 1 วัน)")

            if outfit_to_check and not self.errors:
                overlapping_rentals = CartItem.objects.filter(
                    outfit=outfit_to_check,
                    cart__is_paid=True,
                    start_date__lte=end_date,
                    end_date__gte=start_date
                )
                if self.instance and self.instance.pk:
                    overlapping_rentals = overlapping_rentals.exclude(pk=self.instance.pk)

                if overlapping_rentals.exists():
                    conflict_details_list = [f"{r.start_date.strftime('%d/%m/%y')}-{r.end_date.strftime('%d/%m/%y')}" for r in overlapping_rentals]
                    conflict_msg = "; ".join(conflict_details_list)
                    self.add_error(None, mark_safe(
                        f"ชุดนี้ไม่ว่างในช่วงวันที่คุณเลือก ({start_date.strftime('%d/%m/%y')} - {end_date.strftime('%d/%m/%y')}). " \
                        f"มีผู้เช่าแล้วในช่วง: {conflict_msg}"
                    ))
        return cleaned_data

class PaymentConfirmationForm(forms.Form):
    slip = forms.ImageField(
        label="อัปโหลดสลิปการโอน",
        required=True,
        widget=forms.ClearableFileInput(attrs={'class': 'form-control'})
    )

class CustomerOrderImageUploadForm(forms.ModelForm):
    class Meta:
        model = Cart
        fields = ['customer_uploaded_image']
        widgets = {'customer_uploaded_image': forms.ClearableFileInput(attrs={'class': 'form-control form-control-sm'})}
        labels = {'customer_uploaded_image': 'แนบรูปภาพประกอบปัญหา (ถ้ามี):'}

class ReturnShipmentForm(forms.ModelForm):
    return_tracking_number = forms.CharField(
        label="เลขพัสดุสำหรับส่งคืน",
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control form-control-sm', 'placeholder': 'เช่น TH123456789EX'})
    )
    return_shipment_image = forms.ImageField(
        label="แนบรูปภาพหลักฐานการส่ง (เช่น สลิปขนส่ง)",
        required=False,
        widget=forms.ClearableFileInput(attrs={'class': 'form-control form-control-sm'})
    )

    class Meta:
        model = Cart
        fields = ['return_tracking_number', 'return_shipment_image']