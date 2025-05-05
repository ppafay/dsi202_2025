from django.shortcuts import render, get_object_or_404, redirect
from django.views import View
from .models import Outfit
from .forms import OutfitForm, RentForm
from .models import Product, CartItem, Cart, Outfit

def home(request):
    return render(request, 'outfits/home.html')

class OutfitListView(View):
    def get(self, request):
        outfits = Outfit.objects.all()
        return render(request, 'outfits/list.html', {'outfits': outfits})

class OutfitSearchView(View):
    def get(self, request):
        query = request.GET.get('q')
        results = Outfit.objects.filter(name__icontains=query)
        return render(request, 'outfits/search.html', {'results': results, 'query': query})

class OutfitDetailView(View):
    def get(self, request, pk):
        outfit = get_object_or_404(Outfit, pk=pk)
        form = RentForm()
        return render(request, 'outfits/detail.html', {'outfit': outfit, 'form': form})

    def post(self, request, pk):
        outfit = get_object_or_404(Outfit, pk=pk)
        form = RentForm(request.POST)
        if form.is_valid():
            duration = form.cleaned_data['duration']
            total_price = duration * outfit.price
            outfit.is_rented = True
            outfit.save()
            return render(request, 'outfits/rent_success.html', {
                'outfit': outfit,
                'duration': duration,
                'total_price': total_price
            })
        return render(request, 'outfits/detail.html', {'outfit': outfit, 'form': form})

def create_outfit(request):
    if request.method == 'POST':
        form = OutfitForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('outfit-list')
    else:
        form = OutfitForm()
    return render(request, 'outfits/rental_form.html', {'form': form})

# shop/views.py
def cart_view(request):
    # ... ดึงข้อมูลตะกร้าสินค้าจาก session หรือ database ...
    cart = Cart.objects.first()  # ดึงตะกร้าแรกมาแสดงก่อน (ตัวอย่าง)
    return render(request, 'shop/cart.html', {'cart': cart})

def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    # ... เพิ่มสินค้าลงในตะกร้า ...
    return redirect('cart')  # Redirect ไปยังหน้าตะกร้าสินค้า

def update_cart(request, item_id):
    # ... อัปเดตจำนวนสินค้า ...
    return redirect('cart')

def remove_from_cart(request, item_id):
    # ... ลบสินค้าออกจากตะกร้า ...
    return redirect('cart')
