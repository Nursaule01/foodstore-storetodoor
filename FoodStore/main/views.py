import json
from pprint import pprint

from django.core.files.storage import FileSystemStorage
from django.http import response, JsonResponse, HttpResponse, HttpResponseRedirect
from django.shortcuts import render, redirect

# Create your views here.
from main.models import Address, User, Dish, Product, Cart, CartForm


def index(req):
    if not req.session.get('user'):
        return redirect('/authorize')
    userId = req.session.get('user')

    dish = Dish.objects.first()
    dishes = Dish.objects.all().exclude(pk=dish.id)

    nums = []
    for i in range(1, len(dishes) + 1):
        nums.append(i)

    user = User.objects.get(id=int(userId))
    return render(req, 'index.html', {
        'user': user,
        'first_dish': dish,
        'nums': nums,
        'dishes': dishes,
        'products': Product.objects.all(),
    })


def dishPage(req, dish_id):
    try:
        dish = Dish.objects.get(pk=dish_id)
        ingredients = Product.objects.filter(pk__in=dish.ingredients)
        steps = []
        for i in range(len(dish.cookingSteps)):
            steps.append({
                'number': i + 1,
                'image': dish.cookingSteps[i][0],
                'text': dish.cookingSteps[i][1],
            })
        return render(req, 'dish.html', {
            'dish': dish,
            'ingredients': ingredients,
            'steps': steps
        })
    except:
        return render(req, '404.html')


def authorize(req):
    return render(req, 'authorize.html')


def product(req, product_id):
    currProduct = Product.objects.get(pk=product_id)
    return render(req, 'product.html', {
        'product': currProduct
    })


def login(req):
    if req.method == 'POST':
        username = req.POST['email']
        password = req.POST['pass']

        errors = []
        try:
            user = User.objects.get(email=username, password=password)
            if user is None:
                errors.append('Invalid login or password')

            req.session['user'] = user.id
            return redirect('/', req)

        except User.DoesNotExist:
            errors.append('No users registered')

        if len(errors):
            return render(req, 'authorize.html', {
                'errors': errors
            })

        return render(req, 'authorize.html')


def logout(req):
    del req.session['user']

    return redirect('/authorize')


def register(req):
    if req.method == 'POST':
        # address
        country = req.POST["country"]
        city = req.POST['city']
        street = req.POST['street']
        house = req.POST['house']

        address = Address(
            country=country,
            city=city,
            street=street,
            house=house
        )
        address.save()

        # user
        email = req.POST['email']
        phone = req.POST['phone']
        password = req.POST['pass']
        password2 = req.POST['pass2']

        errors = []

        duplicateUser = User.objects.filter(email=email)
        duplicateNumber = User.objects.filter(phoneNumber=phone)

        if len(duplicateUser):
            errors.append('Email must be unique')

        if len(duplicateNumber):
            errors.append('Number must be unique')

        if password != password2:
            errors.append('Passwords does not match')

        if len(errors):
            return render(req, 'authorize.html', {
                'errors': errors
            })

        name = req.POST['name']
        gender = req.POST['gender']
        new_user = User(
            fullName=name,
            email=email,
            phoneNumber=phone,
            gender=gender,
            password=password,
            address_id=address.id
        )
        new_user.save()

        req.session['user'] = new_user.id

        return redirect('/', req)
        # return render()


def cart(req):
    items = Cart.objects.filter(user_id=req.session['user'])
    sum = 0
    if len(items):
        for item in items:
            sum += item.amount * item.product.price
        return render(req, 'cart.html', {
            'items': items,
            'sum': sum
        })
    return render(req, 'emptyCart.html')


def addProduct(req):
    if req.method == 'POST':
        picture = req.FILES['picture']
        fs = FileSystemStorage()
        filename = fs.save(picture.name, picture)
        uploaded_file_url = fs.url(filename)

        name = req.POST['name']
        description = req.POST['description']
        category = req.POST['category']
        price = req.POST['price']

        newProduct = Product(name=name,
                             description=description,
                             category=category,
                             price=price,
                             picture=uploaded_file_url)
        newProduct.save()

        return render(req, 'addProduct.html')
    return render(req, 'addProduct.html')


def addToCart(req, product_id):
    userCart = Cart(user_id=req.session['user'], product_id=product_id, amount=1)
    userCart.save()
    next = req.GET.get('next', '/')
    return HttpResponseRedirect(next)


def removeFromCart(req, cart_id):
    userCart = Cart.objects.get(pk=cart_id)
    userCart.delete()
    return redirect('cart')


def payment(req):
    items = Cart.objects.filter(user_id=req.session['user'])
    sum = 0
    user = User.objects.get(pk=int(req.session['user']))
    if len(items):
        for item in items:
            sum += item.amount * item.product.price
        return render(req, 'payment.html', {
            'user': user,
            'items': items,
            'sum': sum
        })
    return redirect('cart')


def proceed(req, price):
    user = User.objects.get(pk=int(req.session['user']))
    user.balance -= price
    if user.balance < price:
        return render(req, 'notEnough.html')
    user.save()
    items = Cart.objects.filter(user_id=req.session['user'])
    items.delete()
    return redirect('index')


def updateCartProductAmount(req, cart_id, amount):
    pprint(cart_id)
    pprint(amount)
    cartItem = Cart.objects.get(pk=int(cart_id))
    cartItem.amount = int(amount)
    cartItem.save()
    return HttpResponse(status=200)


def addDish(req):
    if req.method == 'POST':
        picture = req.FILES['picture']
        fs = FileSystemStorage()
        filename = fs.save(picture.name, picture)
        uploaded_file_url = fs.url(filename)

        name = req.POST['name']
        ingredients = req.POST.getlist('ingredient_ids[]')

        dish = Dish(picture=uploaded_file_url, name=name, ingredients=ingredients, cookingSteps=[])
        dish.save()

        return render(req, 'addDish.html')
    return render(req, 'addDish.html', {
        'ingredients': Product.objects.all()
    })


def addStep(req):
    if req.method == 'POST':
        picture = req.FILES['picture']
        fs = FileSystemStorage()
        filename = fs.save(picture.name, picture)
        uploaded_file_url = fs.url(filename)

        dish_id = req.POST['dish_id']
        text = req.POST['text']

        dish = Dish.objects.get(pk=dish_id)
        if dish.cookingSteps is None:
            dish.cookingSteps = []
        dish.cookingSteps.append([uploaded_file_url, text])
        dish.save()

    return render(req, 'addStep.html', {
        "dishes": Dish.objects.all()
    })
