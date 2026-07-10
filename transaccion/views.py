import json
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, DeleteView

from billing.models import Product
from shared.money import compute_totals

from .models import Transaccion
from .forms import TransaccionForm, TransaccionDetailFormSet


class TransaccionListView(LoginRequiredMixin, ListView):
    model = Transaccion
    template_name = 'transaccion/transaccion_list.html'
    context_object_name = 'transacciones'


class TransaccionDetailView(LoginRequiredMixin, DetailView):
    model = Transaccion
    template_name = 'transaccion/transaccion_detail.html'
    context_object_name = 'transaccion'


class TransaccionDeleteView(LoginRequiredMixin, DeleteView):
    model = Transaccion
    template_name = 'transaccion/transaccion_confirm_delete.html'
    success_url = reverse_lazy('transaccion_list')


# ─── Crear Transacción (con productos + stock) ─────────────────────────────

@login_required
def transaccion_create(request):
    if request.method == 'POST':
        form = TransaccionForm(request.POST)
        formset = TransaccionDetailFormSet(request.POST)

        if form.is_valid() and formset.is_valid():
            has_detail = any(
                f.cleaned_data.get('product') and not f.cleaned_data.get('DELETE')
                for f in formset.forms
            )
            if not has_detail:
                messages.error(request, 'Debes agregar al menos un producto.')
            else:
                # Calcular total desde los productos
                subtotal = Decimal('0')
                for f in formset.forms:
                    cd = f.cleaned_data
                    if not cd or cd.get('DELETE'):
                        continue
                    qty = cd.get('quantity', 0)
                    price = cd.get('unit_price', 0)
                    subtotal += qty * price

                subtotal, tax, total = compute_totals(subtotal)

                # Validar stock si es venta (ingreso)
                if form.cleaned_data['tipo'] == 'ingreso':
                    needed = {}
                    for f in formset.forms:
                        cd = f.cleaned_data
                        if not cd or cd.get('DELETE'):
                            continue
                        p = cd.get('product')
                        if not p:
                            continue
                        needed[p.id] = needed.get(p.id, 0) + cd.get('quantity', 0)

                    faltante = None
                    for pid, qty in needed.items():
                        prod = Product.objects.get(pk=pid)
                        if prod.stock < qty:
                            faltante = prod
                            break

                    if faltante is not None:
                        messages.error(
                            request,
                            f'Stock insuficiente para "{faltante.name}": '
                            f'hay {faltante.stock} y se necesitan {needed[faltante.id]}.'
                        )
                        return render(request, 'transaccion/transaccion_form.html', {
                            'form': form,
                            'formset': formset,
                        })

                with transaction.atomic():
                    t = form.save(commit=False)
                    t.monto = total
                    t.iva = tax
                    t.save()

                    formset.instance = t
                    formset.save()

                    # Ajustar stock
                    for f in formset.forms:
                        cd = f.cleaned_data
                        if not cd or cd.get('DELETE'):
                            continue
                        prod = cd['product']
                        qty = cd['quantity']
                        if t.tipo == 'ingreso':  # Venta → resta stock
                            prod.stock -= qty
                        else:                     # Compra → suma stock
                            prod.stock += qty
                        prod.save(update_fields=['stock'])

                messages.success(request, f'Transacción #{t.id} creada. Total: ${t.total}')
                return redirect('transaccion_list')
    else:
        form = TransaccionForm()
        formset = TransaccionDetailFormSet()

    product_prices = {
        str(p.id): str(p.unit_price)
        for p in Product.objects.filter(is_active=True)
    }

    return render(request, 'transaccion/transaccion_form.html', {
        'form': form,
        'formset': formset,
        'product_prices_json': json.dumps(product_prices),
    })


# ─── Editar Transacción ──────────────────────────────────────────────────

@login_required
def transaccion_update(request, pk):
    t = get_object_or_404(Transaccion.objects.prefetch_related('detalles__product'), pk=pk)

    if request.method == 'POST':
        form = TransaccionForm(request.POST, instance=t)
        formset = TransaccionDetailFormSet(request.POST, instance=t)

        if form.is_valid() and formset.is_valid():
            has_detail = any(
                f.cleaned_data.get('product') and not f.cleaned_data.get('DELETE')
                for f in formset.forms
            )
            if not has_detail:
                messages.error(request, 'Debes agregar al menos un producto.')
            else:
                # Calcular total desde los productos
                subtotal = Decimal('0')
                for f in formset.forms:
                    cd = f.cleaned_data
                    if not cd or cd.get('DELETE'):
                        continue
                    qty = cd.get('quantity', 0)
                    price = cd.get('unit_price', 0)
                    subtotal += qty * price

                subtotal, tax, total = compute_totals(subtotal)

                # Cantidades anteriores para revertir stock
                old_qty = {}
                for d in t.detalles.all():
                    old_qty[d.product_id] = old_qty.get(d.product_id, 0) + d.quantity

                new_qty = {}
                for f in formset.forms:
                    cd = f.cleaned_data
                    if not cd or cd.get('DELETE'):
                        continue
                    p = cd.get('product')
                    if not p:
                        continue
                    new_qty[p.id] = new_qty.get(p.id, 0) + cd.get('quantity', 0)

                # Validar stock si es venta (ingreso)
                if form.cleaned_data['tipo'] == 'ingreso':
                    faltante = None
                    for pid in set(old_qty) | set(new_qty):
                        delta = new_qty.get(pid, 0) - old_qty.get(pid, 0)
                        prod = Product.objects.get(pk=pid)
                        if prod.stock - delta < 0:
                            faltante = prod
                            break
                    if faltante is not None:
                        messages.error(
                            request,
                            f'Stock insuficiente para "{faltante.name}".'
                        )
                        return render(request, 'transaccion/transaccion_form.html', {
                            'form': form,
                            'formset': formset,
                            'product_prices_json': json.dumps({
                                str(p.id): str(p.unit_price)
                                for p in Product.objects.filter(is_active=True)
                            }),
                        })

                with transaction.atomic():
                    t = form.save(commit=False)
                    t.monto = total
                    t.iva = tax
                    t.save()

                    formset.instance = t
                    formset.save()

                    # Ajustar stock por diferencia
                    for pid in set(old_qty) | set(new_qty):
                        delta = new_qty.get(pid, 0) - old_qty.get(pid, 0)
                        if delta:
                            prod = Product.objects.get(pk=pid)
                            if t.tipo == 'ingreso':
                                prod.stock -= delta
                            else:
                                prod.stock += delta
                            prod.save(update_fields=['stock'])

                messages.success(request, f'Transacción #{t.id} actualizada.')
                return redirect('transaccion_detail', pk=t.pk)
    else:
        form = TransaccionForm(instance=t)
        formset = TransaccionDetailFormSet(instance=t)

    product_prices = {
        str(p.id): str(p.unit_price)
        for p in Product.objects.filter(is_active=True)
    }

    return render(request, 'transaccion/transaccion_form.html', {
        'form': form,
        'formset': formset,
        'product_prices_json': json.dumps(product_prices),
        'is_edit': True,
        'object': t,
    })