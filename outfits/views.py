from django.shortcuts import render, get_object_or_404, redirect
from django.views import View
from .models import Outfit
from .forms import OutfitForm, RentForm
from .models import Product, CartItem, Cart  # นำเข้าโมเดลของคุณ

def home(request):
    """
    แสดงหน้าหลักของเว็บไซต์
    """
    return render(request, 'outfits/home.html')

class OutfitListView(View):
    """
    แสดงรายการชุดทั้งหมด
    """
    def get(self, request):
        outfits = Outfit.objects.all()
        return render(request, 'outfits/list.html', {'outfits': outfits})

class OutfitSearchView(View):
    """
    ค้นหาชุดตามชื่อ
    """
    def get(self, request):
        query = request.GET.get('q')
        results = Outfit.objects.filter(name__icontains=query)
        return render(request, 'outfits/search.html', {'results': results, 'query': query})

class OutfitDetailView(View):
    """
    แสดงรายละเอียดของชุดแต่ละชุด
    """
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
    """
    สร้างชุดใหม่
    """
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
    """
    แสดงตะกร้าสินค้าของผู้ใช้
    """
    cart_id = request.session.get('cart_id')  # ลองดึง cart_id จาก session
    if cart_id:
        try:
            cart = Cart.objects.get(id=cart_id)
        except Cart.DoesNotExist:
            cart = Cart.objects.create()
            request.session['cart_id'] = cart.id  # บันทึก cart_id ลงใน session
    else:
        cart = Cart.objects.create()
        request.session['cart_id'] = cart.id  # บันทึก cart_id ลงใน session

    return render(request, 'shop/cart.html', {'cart': cart})


def add_to_cart(request, product_id):
    """
    เพิ่มสินค้าไปยังตะกร้าของผู้ใช้
    """
    product = get_object_or_404(Product, id=product_id)
    cart_id = request.session.get('cart_id')
    if cart_id:
        try:
            cart = Cart.objects.get(id=cart_id)
        except Cart.DoesNotExist:
            cart = Cart.objects.create()
            request.session['cart_id'] = cart.id
    else:
        cart = Cart.objects.create()
        request.session['cart_id'] = cart.id

    # ตรวจสอบว่ามีสินค้านี้อยู่ในตะกร้าแล้วหรือไม่
    try:
        cart_item = CartItem.objects.get(cart=cart, product=product)
        cart_item.quantity += 1
        cart_item.save()
    except CartItem.DoesNotExist:
        # สินค้ายังไม่มีในตะกร้า สร้าง CartItem ใหม่
        cart_item = CartItem.objects.create(cart=cart, product=product, quantity=1)

    cart.get_total_price()
    return redirect('cart')


def update_cart(request, item_id):
    """
    อัปเดตจำนวนสินค้าในตะกร้าของผู้ใช้
    """
    cart_id = request.session.get('cart_id')
    if cart_id:
        try:
            cart = Cart.objects.get(id=cart_id)
        except Cart.DoesNotExist:
            cart = Cart.objects.create()
            request.session['cart_id'] = cart.id
    else:
        cart = Cart.objects.create()
        request.session['cart_id'] = cart.id

    cart_item = get_object_or_404(CartItem, id=item_id, cart=cart)
    quantity = int(request.GET.get('quantity', 1))
    if quantity > 0:
        cart_item.quantity = quantity
        cart_item.save()
    else:
        cart_item.delete()
    cart.get_total_price()
    return redirect('cart')

def remove_from_cart(request, item_id):
    """
    ลบสินค้าออกจากตะกร้าของผู้ใช้
    """
 # project/main/dsi202/outfits/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.views import View
from .models import Outfit, CartItem, Cart # ลบ Product ถ้าไม่ได้ใช้
from .forms import OutfitForm, RentForm

# ... (views อื่นๆ ที่มีอยู่ เช่น home, OutfitListView, etc.) ...

def add_to_cart(request, outfit_id): # เปลี่ยน product_id เป็น outfit_id
    """
    เพิ่มสินค้า (Outfit) ไปยังตะกร้าของผู้ใช้
    """
    outfit_obj = get_object_or_404(Outfit, id=outfit_id) # ดึง Outfit object
    cart_id = request.session.get('cart_id')
    if cart_id:
        try:
            cart = Cart.objects.get(id=cart_id)
        except Cart.DoesNotExist:
            cart = Cart.objects.create()
            request.session['cart_id'] = cart.id
    else:
        cart = Cart.objects.create()
        request.session['cart_id'] = cart.id

    # ตรวจสอบว่ามีสินค้านี้อยู่ในตะกร้าแล้วหรือไม่
    try:
        # ใช้ outfit=outfit_obj ในการ query CartItem
        cart_item = CartItem.objects.get(cart=cart, outfit=outfit_obj)
        cart_item.quantity += 1
        cart_item.save()
    except CartItem.DoesNotExist:
        # สินค้ายังไม่มีในตะกร้า สร้าง CartItem ใหม่โดยใช้ outfit=outfit_obj
        cart_item = CartItem.objects.create(cart=cart, outfit=outfit_obj, quantity=1)

    cart.get_total_price() # อัปเดตราคารวมของตะกร้า
    return redirect('cart') # หรือจะ redirect ไปหน้าอื่นตามต้องการ

# cart_view, update_cart, remove_from_cart ควรตรวจสอบการอ้างอิงถึงราคาสินค้า
# ให้แน่ใจว่าใช้ item.outfit.price และ Cart.get_total_price() ทำงานถูกต้องแล้ว

def cart_view(request):
    """
    แสดงตะกร้าสินค้าของผู้ใช้
    """
    cart_id = request.session.get('cart_id')
    cart = None
    if cart_id:
        try:
            cart = Cart.objects.get(id=cart_id)
            cart.get_total_price() # คำนวณราคารวมใหม่ทุกครั้งที่ดูตะกร้า
        except Cart.DoesNotExist:
            # ถ้า cart_id ใน session ไม่ถูกต้อง ก็สร้างตะกร้าใหม่
            cart = Cart.objects.create()
            request.session['cart_id'] = cart.id
    else:
        # ถ้าไม่มี cart_id ใน session เลย ก็สร้างตะกร้าใหม่
        cart = Cart.objects.create()
        request.session['cart_id'] = cart.id
    
    # ส่ง related_name ที่ถูกต้องไปยัง template
    return render(request, 'shop/cart.html', {'cart': cart, 'cart_items_list': cart.cart_items_cart.all() if cart else []})


def update_cart(request, item_id): # item_id คือ ID ของ CartItem
    """
    อัปเดตจำนวนสินค้าในตะกร้าของผู้ใช้
    """
    cart_id = request.session.get('cart_id')
    if not cart_id:
        return redirect('cart') # ไม่มีตะกร้า ก็กลับไปหน้าตะกร้า (ซึ่งจะสร้างตะกร้าใหม่)

    try:
        cart = Cart.objects.get(id=cart_id)
    except Cart.DoesNotExist:
        return redirect('cart') # ตะกร้าไม่ถูกต้อง

    cart_item = get_object_or_404(CartItem, id=item_id, cart=cart)
    
    # ตรวจสอบว่า request.POST หรือ request.GET สำหรับ quantity
    if request.method == 'POST':
        quantity = int(request.POST.get('quantity', 1))
    else: # สำหรับกรณีที่อาจจะส่งผ่าน GET (ไม่แนะนำสำหรับการเปลี่ยนแปลงข้อมูล)
        quantity = int(request.GET.get('quantity', cart_item.quantity))

    if quantity > 0:
        cart_item.quantity = quantity
        cart_item.save()
    else:
        cart_item.delete() # ถ้าจำนวนเป็น 0 หรือน้อยกว่า ให้ลบออกจากตะกร้า
    
    cart.get_total_price() # อัปเดตราคารวม
    return redirect('cart')

def remove_from_cart(request, item_id): # item_id คือ ID ของ CartItem
    """
    ลบสินค้าออกจากตะกร้าของผู้ใช้
    """
    cart_id = request.session.get('cart_id')
    if not cart_id:
        return redirect('cart')

    try:
        cart = Cart.objects.get(id=cart_id)
    except Cart.DoesNotExist:
        return redirect('cart')
        
    cart_item = get_object_or_404(CartItem, id=item_id, cart=cart)
    cart_item.delete()
    cart.get_total_price() # อัปเดตราคารวม
    return redirect('cart')

# ... (views อื่นๆ) ...   cart_id = request.session.get('cart_id')
    if cart_id:
        try:
            cart = Cart.objects.get(id=cart_id)
        except Cart.DoesNotExist:
            cart = Cart.objects.create()
            request.session['cart_id'] = cart.id
    else:
        cart = Cart.objects.create()
        request.session['cart_id'] = cart.id

    cart_item = get_object_or_404(CartItem, id=item_id, cart=cart)
    cart_item.delete()
    cart.get_total_price()
    return redirect('cart')
def user_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, "Invalid username or password.")
    return render(request, 'accounts/login.html')

def user_logout(request):
    logout(request)
    return redirect('home')

def user_register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Account created successfully.")
            return redirect('login')
        else:
            messages.error(request, "Please correct the error below.")
    else:
        form = UserCreationForm()
    return render(request, 'accounts/register.html', {'form': form})