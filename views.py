from django.shortcuts import render
from customer_data.models import *
from django.utils.encoding import smart_str, smart_unicode
import simplejson
import json
import MySQLdb
from django.http import HttpResponse
from django.core.cache import cache, caches

def index(request):
    lines_records = Productlines.objects.all()
    emp_records = Employees.objects.all()

    product_data = []
    productlines_data = []
    prod_and_lines = {}
    emp_records_output = []
    productcode_order = {}

    order_date_vs_orders = {}

    for emp in emp_records:
        emp_records_output.append(', '.join((str(emp.lastname), str(emp.firstname))))

    for pl in lines_records:
        productlines_data.append(str(pl.productline))
        prod_and_lines.setdefault(str(pl.productline), [])
        product_records = Products.objects.filter(productline=pl.productline)

        for pd in product_records:
            try:
                product_data.append(str(pd.productname.replace(u'\u2019', "'")))
            except:
                import pdb;pdb.set_trace()

            prod_and_lines[str(pl.productline)].append(str(pd.productname.replace(u'\u2019', "'")))

            orderdetails_records = Orderdetails.objects.filter(productcode=str(pd.productcode))
            productcode_order.setdefault(str(pd.productcode), [])

            for ordr in orderdetails_records:
                productcode_order[str(pd.productcode)].append(str(ordr.ordernumber.ordernumber))

            orders_records = Orders.objects.filter(ordernumber=str(ordr.ordernumber.ordernumber))
            for orecord in orders_records:
                order_date_vs_orders.setdefault(orecord.orderdate, [])
                order_date_vs_orders[orecord.orderdate].append(str(orecord.ordernumber))

    return render(request, 'index.html',
                  {'product_data': product_data,
                   'productlines_data': productlines_data, 'prod_and_lines': prod_and_lines,
                   'emp_records_output': emp_records_output, 'productcode_order': productcode_order,
                   'order_date_vs_orders': order_date_vs_orders})


def mysql_connection(db_name='classicmodels'):
    conn = MySQLdb.connect(db=db_name, host='localhost', user='root', passwd='python@123')
    cursor = conn.cursor()
    return conn, cursor

def layout(request):

    layout_product_data = [cache_products(product=product)]
    layout_productlines_data = [cache_plines(plines=None)]

    return render(request, 'layout.html', {'layout_productlines_data': layout_productlines_data, 'layout_product_data': layout_product_data, })

def display(request):
    from_date = request.GET['from']
    to_date = request.GET['to']
    input_productline = request.GET['json1']
    input_product = request.GET['json2']
    salesmen = json.loads(request.GET['json3'], '[]')
    lastName, firstName = salesmen[0].split(',')
    tName, firstName = lastName.strip(), firstName.strip()

    processed_records = []
    conn, cursor = mysql_connection()
    query = 'select customerName, contactLastName, contactFirstName, employeeNumber, lastName, firstName, jobTitle, customerNumber, customerName from employees, customers where employeeNumber = salesRepEmployeeNumber and lastName = "%s" and firstName = "%s"' % (
    lastName, firstName)
    cursor.execute(query)
    records = cursor.fetchall()
    for record in records:
        customerName, contactLastName, contactFirstName, employeeNumber, lastName, firstName, jobTitle, customerNumber, customerName = record
        query = 'select orderDate, status, productCode from orderdetails D, orders O where O.orderNumber=D.orderNumber and customerNumber = "%s" and orderDate between %s and %s' % (
        customerNumber, from_date, to_date)
        cursor.execute(query)
        order_records = cursor.fetchall()
        for o_record in order_records:
            orderDate, status, productCode = o_record
            orderDate = str(orderDate)
            query = 'select productName from productlines L, products P where L.productLine = P.productLine and productCode = "%s" and productName=%s and P.productLine=%s' % (
            productCode, input_product, input_productline)
            cursor.execute(query)
            p_records = cursor.fetchall()

            for p_record in p_records:
                productName = p_record[0]

                output = {'lastName': lastName, 'firstName': firstName,
                          'productCode': productCode, 'customerName': customerName, 'jobTitle': jobTitle,
                          'customerName': customerName, 'contactLastName': contactLastName,
                          'contactFirstName': contactFirstName, 'orderDate': orderDate, 'status': status,
                          }
                processed_records.append(output)
    # import pdb;pdb.set_trace()

    return HttpResponse(simplejson.dumps({'dtable': processed_records}), content_type="application/json")

def react(request):
    return render(request, 'react.html')

def cache_plines(plines=None):
    cached_data_plines = cache.get(plines)
    conn, cursor = mysql_connection()
    if not cached_data_plines:
        query = 'select productLine from productLines'
        cursor.execute(query)
        plines = cursor.fetchall()
    else:
        cached_data_plines = cache.set('plines', plines, 60)
        import pdb; pdb.set_trace()
    return plines

def cache_products(product):
    cached_data_products = cache.get('product')
    conn, cursor = mysql_connection()
    if not cached_data_products:
        query = 'select productName from products'
        cursor.execute(query)
        product = cursor.fetchall()
    else:
        cached_data_products = cache.set('products', product, 60)
    return product