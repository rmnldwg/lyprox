import numpy as np
import factory
from factory.django import DjangoModelFactory
from faker import Faker
fake = Faker()
# Faker.seed(42)

from accounts.models import User, Institution
from patients.models import Patient, Tumor, Diagnose


class InstitutionFactory(DjangoModelFactory):
    class Meta:
        model = Institution
    
    name = f"{fake.name()} Hospital"
    city = fake.city()
    street = f"{fake.street_name()} {np.random.randint(low=1, high=255)}"
    country = fake.country()
    phone = fake.phone_number()
    shortname = "".join([w[0].upper() for w in f"{name} {city}".split(" ")])


class UserFactory(DjangoModelFactory):
    class Meta:
        model = User
    
    institution = factory.SubFactory(InstitutionFactory)
    
    first_name = fake.first_name()
    last_name = fake.last_name()
    email = f"{first_name.lower()}.{last_name.lower()}@mail.com"
    is_staff = False
    is_superuser = False
    
    password = fake.password()


class PatientFactory(DjangoModelFactory):
    class Meta:
        model = Patient
    
    class Params:
        first_name = fake.first_name()
        last_name = fake.last_name()
        birthday = fake.date_of_birth(minimum_age=14)
    
    hash_value = factory.LazyAttribute(
        lambda o: hash((o.first_name, o.last_name, o.birthday))
    )
    gender = fake.random_element(elements=["male", "female"])
    diagnose_date = factory.LazyAttribute(
        lambda o: fake.date_between_dates(date_start=o.birthday)
    )
    age = factory.LazyAttribute(
        lambda o: o.diagnose_date.year - o.birthday.year
    )
    
    alcohol_abuse = fake.random_element(elements=[True, False, None])
    nicotine_abuse = fake.random_element(elements=[True, False, None])
    hpv_status = fake.random_element(elements=[True, False, None])
    neck_dissection = fake.random_element(elements=[True, False, None])
    
    t_stage = fake.random_element(elements=Patient.T_stages.values)
    n_stage = fake.random_element(elements=Patient.N_stages.values)
    m_stage = fake.random_element(elements=Patient.M_stages.values)
    
    institution = factory.SubFactory(InstitutionFactory)