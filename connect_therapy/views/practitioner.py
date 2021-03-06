from datetime import timedelta

from django.contrib.auth import update_session_auth_hash, views as auth_views
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.sites.shortcuts import get_current_site
from django.http.response import HttpResponseRedirect
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views import generic
from django.views.generic import FormView, UpdateView, DeleteView, DetailView
from django.views.generic.edit import FormMixin

from connect_therapy import notifications
from connect_therapy.emails import send_practitioner_confirm_email
from connect_therapy.forms.practitioner.practitioner import *
from connect_therapy.models import Practitioner, Appointment


class PractitionerSignUpView(FormView):
    form_class = PractitionerSignUpForm
    template_name = 'connect_therapy/practitioner/signup.html'
    success_url = reverse_lazy('connect_therapy:index')

    def form_valid(self, form):
        user = form.save(commit=False)
        user.username = user.email
        user.save()
        practitioner = Practitioner(
            user=user,
            address_line_1=form.cleaned_data['address_line_1'],
            address_line_2=form.cleaned_data['address_line_2'],
            postcode=form.cleaned_data['postcode'],
            mobile=form.cleaned_data['mobile'],
            bio=form.cleaned_data['bio']
        )
        practitioner.save()
        send_practitioner_confirm_email(practitioner, get_current_site(self.request))
        return super().form_valid(form)


class PractitionerLoginView(auth_views.LoginView):
    template_name = 'connect_therapy/practitioner/login.html'
    authentication_form = PractitionerLoginForm

    def get_success_url(self):
        return reverse_lazy('connect_therapy:practitioner-homepage')


class PractitionerNotesView(FormMixin, UserPassesTestMixin, DetailView):
    form_class = PractitionerNotesForm
    template_name = 'connect_therapy/practitioner/notes.html'
    success_url = reverse_lazy('connect_therapy:practitioner-my-appointments')
    login_url = reverse_lazy('connect_therapy:practitioner-login')
    redirect_field_name = None
    model = Appointment

    def test_func(self):
        try:
            self.request.user.practitioner
        except (Practitioner.DoesNotExist, AttributeError, TypeError) as e:
            return False
        return self.get_object() is not None and \
               self.request.user.id == self.get_object().practitioner.user.id and \
               self.get_object().practitioner.email_confirmed and \
               self.get_object().practitioner.is_approved

    def form_valid(self, form):
        self.object.practitioner_notes = form.cleaned_data['practitioner_notes']
        self.object.patient_notes_by_practitioner = form.cleaned_data['patient_notes_by_practitioner']
        self.object.save()
        return super().form_valid(form)

    def post(self, request, **kwargs):
        self.object = self.get_object()
        form = self.get_form()
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)


class PractitionerMyAppointmentsView(UserPassesTestMixin, generic.TemplateView):
    template_name = 'connect_therapy/practitioner/my-appointments.html'
    login_url = reverse_lazy('connect_therapy:practitioner-login')
    redirect_field_name = None
    model = Appointment

    def test_func(self):
        try:
            practitioner = Practitioner.objects.get(user=self.request.user)
            return practitioner.email_confirmed and practitioner.is_approved
        except (Practitioner.DoesNotExist, AttributeError, TypeError) as e:
            return False

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(**kwargs)
        context['booked_appointments'] = Appointment.objects.filter(
            start_date_and_time__gte=timezone.now() - timedelta(minutes=30),
            patient__isnull=False,
            practitioner=self.request.user.practitioner

        ).order_by('-start_date_and_time')
        context['unbooked_appointments'] = Appointment.objects.filter(
            start_date_and_time__gte=timezone.now(),
            patient__isnull=True,
            practitioner=self.request.user.practitioner
        ).order_by('-start_date_and_time')
        context['needing_notes'] = Appointment.objects.filter(
            start_date_and_time__lt=timezone.now() - timedelta(minutes=30),
            patient_notes_by_practitioner="",
            practitioner=self.request.user.practitioner,
            patient__isnull=False
        ).order_by('-start_date_and_time')
        context['past_appointments'] = Appointment.objects.filter(
            start_date_and_time__lt=timezone.now() - timedelta(minutes=30),
            practitioner=self.request.user.practitioner
        ).exclude(
            patient_notes_by_practitioner="").order_by('-start_date_and_time')

        return context


class PractitionerPreviousNotesView(UserPassesTestMixin, generic.DetailView):
    login_url = reverse_lazy('connect_therapy:practitioner-my-appointments')
    redirect_field_name = None
    model = Appointment
    template_name = 'connect_therapy/practitioner/appointment-notes.html'

    def test_func(self):
        try:
            self.request.user.practitioner
        except (Practitioner.DoesNotExist, AttributeError, TypeError) as e:
            return False
        return self.get_object() is not None and \
               self.request.user.id == self.get_object().practitioner.user.id and \
               self.get_object().practitioner.email_confirmed and \
               self.get_object().practitioner.is_approved


class PractitionerCurrentNotesView(UserPassesTestMixin, generic.DetailView):
    login_url = reverse_lazy('connect_therapy:practitioner-login')
    redirect_field_name = None
    model = Appointment
    template_name = 'connect_therapy/practitioner/before-meeting-notes.html'

    def test_func(self):
        try:
            self.request.user.practitioner
        except (Practitioner.DoesNotExist, AttributeError, TypeError) as e:
            return False
        return self.get_object() is not None and \
               self.request.user.id == self.get_object().practitioner.user.id and \
               self.get_object().practitioner.email_confirmed and \
               self.get_object().practitioner.is_approved


class PractitionerAllPatientsView(UserPassesTestMixin, generic.TemplateView):
    template_name = 'connect_therapy/practitioner/view-patients.html'
    model = Appointment
    login_url = reverse_lazy('connect_therapy:practitioner-login')
    redirect_field_name = None

    def test_func(self):
        try:
            practitioner = self.request.user.practitioner
            return practitioner.email_confirmed and practitioner.is_approved
        except (Practitioner.DoesNotExist, AttributeError, TypeError) as e:
            return False

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        appointments = Appointment.objects.filter(
            practitioner=self.request.user.practitioner
        ).order_by('-start_date_and_time')
        patients_already_seen = []
        appointments_unique_patient = []
        for appointment in appointments:
            if appointment.patient not in patients_already_seen:
                appointments_unique_patient.append(appointment)
                patients_already_seen.append(appointment.patient)
        context['appointments'] = appointments_unique_patient
        return context


class PractitionerProfile(UserPassesTestMixin, generic.TemplateView):
    template_name = 'connect_therapy/practitioner/profile.html'
    model = Practitioner
    login_url = reverse_lazy('connect_therapy:practitioner-login')
    redirect_field_name = None

    def test_func(self):
        try:
            practitioner = self.request.user.practitioner
            return practitioner.email_confirmed and practitioner.is_approved
        except (Practitioner.DoesNotExist, AttributeError, TypeError) as e:
            return False


class PractitionerEditDetailsView(UserPassesTestMixin, UpdateView):
    model = Practitioner
    template_name = 'connect_therapy/practitioner/edit-profile.html'
    form_class = PractitionerEditMultiForm
    success_url = reverse_lazy('connect_therapy:practitioner-profile')
    login_url = reverse_lazy('connect_therapy:practitioner-login')
    redirect_field_name = None

    def test_func(self):
        try:
            self.request.user.practitioner
        except (Practitioner.DoesNotExist, AttributeError, TypeError) as e:
            return False
        return self.get_object() is not None and \
               self.request.user.id == self.get_object().user.id and \
               self.get_object().email_confirmed and \
               self.get_object().is_approved

    def form_valid(self, form):
        self.object.user.username = form.cleaned_data['user']['email']
        self.object.user.save()
        return super().form_valid(form)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.get_form()
        try:
            user = User.objects.get(username=form.cleaned_data['user']['email'])
            if user == self.object.user and form.is_valid():
                return self.form_valid(form)
        except User.DoesNotExist:
            if form.is_valid():
                return self.form_valid(form)

        return self.form_invalid(form)

    def get_form_kwargs(self):
        kwargs = super(PractitionerEditDetailsView, self).get_form_kwargs()
        kwargs.update(instance={
            'user': self.object.user,
            'practitioner': self.object,
        })
        return kwargs


@login_required
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(data=request.POST, user=request.user)

        if form.is_valid():
            form.save()
            update_session_auth_hash(request, form.user)
            return redirect(reverse_lazy('connect_therapy:practitioner-profile'))
        else:
            return redirect(reverse_lazy('connect_therapy:practitioner-change-password'))
    else:
        form = PasswordChangeForm(user=request.user)
        args = {'form': form}
        return render(request, 'connect_therapy/practitioner/change-password.html', args)


class PractitionerSetAppointmentView(UserPassesTestMixin, LoginRequiredMixin, FormView):
    login_url = reverse_lazy('connect_therapy:practitioner-login')
    form_class = PractitionerDefineAppointmentForm
    template_name = 'connect_therapy/practitioner/set-appointment-page.html'
    success_url = reverse_lazy('connect_therapy:practitioner-my-appointments')
    redirect_field_name = None
    model = Practitioner

    def test_func(self):
        try:
            practitioner = self.request.user.practitioner
            return practitioner.email_confirmed and practitioner.is_approved
        except (Practitioner.DoesNotExist, AttributeError, TypeError) as e:
            return False

    def post(self, request, **kwargs):
        hour = 0
        minute = (Appointment._meta.get_field('length').get_default().seconds % 3600) // 60
        form = PractitionerDefineAppointmentForm(request.POST)
        print(form.is_valid())
        if form.is_valid():
            duration = decompress_duration(form.cleaned_data['length'])
            hour = duration[0]
            minute = duration[1]

            appointment = Appointment(
                patient=None,
                practitioner=self.request.user.practitioner,
                start_date_and_time=form.cleaned_data['start_date_and_time'],
                length=timedelta(hours=hour, minutes=minute)
            )

            over_lap_free, over_laps = Appointment.get_appointment__practitioner_overlaps(appointment,
                                                                                          self.request.user.practitioner)
            if not over_lap_free:
                clashes = over_laps
                return render(self.request, 'connect_therapy/practitioner/appointment-overlap.html',
                              context={"clashes": clashes})
            else:
                Appointment.split_merged_appointment(
                    appointment)  # This method will split if needed and then save the appointment
                return super().post(request)

        context = self.get_context_data()
        context['form_was_valid'] = False
        return render(request, self.get_template_names(), context=context)


class PractitionerAppointmentDelete(DeleteView, UserPassesTestMixin):
    model = Appointment
    template_name = 'connect_therapy/practitioner/appointment-cancel.html'
    fields = ['practitioner', 'patient', 'start_date_and_time', 'length', 'practitioner_notes',
              'patient_notes_by_practitioner']
    success_url = reverse_lazy('connect_therapy:practitioner-my-appointments')
    login_url = reverse_lazy('connect_therapy:practitioner-login')
    redirect_field_name = None

    def test_func(self):
        try:
            self.request.user.practitioner
        except (Practitioner.DoesNotExist, AttributeError, TypeError):
            return False
        return self.get_object() is not None and \
               self.request.user.id == self.get_object().practitioner.user.id and \
               self.get_object().practitioner.email_confirmed and \
               self.get_object().practitioner.is_approved

    def delete(self, request, *args, **kwargs):
        message = request.POST['cancel-message']
        self.object = self.get_object()
        notifications.appointment_cancelled_by_practitioner(self.object, message)
        success_url = self.get_success_url()
        self.object.delete()
        return HttpResponseRedirect(success_url)


class PractitionerHomepageView(UserPassesTestMixin, generic.TemplateView):
    template_name = 'connect_therapy/practitioner/homepage.html'
    login_url = reverse_lazy('connect_therapy:practitioner-login')
    redirect_field_name = None
    model = Appointment

    def test_func(self):
        try:
            practitioner = Practitioner.objects.get(user=self.request.user)
            return practitioner.email_confirmed and practitioner.is_approved
        except (Practitioner.DoesNotExist, AttributeError, TypeError) as e:
            return False
