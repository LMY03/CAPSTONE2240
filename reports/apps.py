from django.apps import AppConfig
from django.db.models.signals import post_migrate


class ReportsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'reports'

    def ready(self):
        from django.contrib.auth.hashers import make_password
        from random import choice, choices, randint
        from datetime import timedelta
        from django.utils import timezone

        from proxmox.views import generate_vm_ids, generate_vm_names

        from ticketing.models import RequestEntry, RequestUseCase, IssueTicket
        from proxmox.models import VMTemplates, VirtualMachines, Nodes
        from guacamole.models import GuacamoleConnection
        from users.models import User

        from users.models import User

        def create_initial_users(sender, **kwargs):
            if not User.objects.exists():
                User.objects.create(
                    username='admin',
                    password=make_password('123456'),
                    email='',
                    is_superuser=True,
                    is_staff=True,
                    is_active=True,
                    user_type=User.UserType.TSG
                )
                User.objects.create(
                    username='john.doe',
                    password=make_password('123456'),
                    first_name='John',
                    last_name='Doe',
                    email='',
                    is_staff=False,
                    is_active=True,
                    user_type=User.UserType.TSG
                )
                User.objects.create(
                    username='josephine.cruz',
                    password=make_password('123456'),
                    first_name='Josephine',
                    last_name='Cruz',
                    email='',
                    is_staff=False,
                    is_active=True,
                    user_type=User.UserType.FACULTY
                )

        def create_initial_nodes(sender, **kwargs):
            if not Nodes.objects.exists():
                Nodes.objects.create(
                    name='pve',
                )
                Nodes.objects.create(
                    name='jin',
                )

        def create_initial_vm_templates(sender, **kwargs):
            if not VMTemplates.objects.exists():
                VMTemplates.objects.create(
                    vm_id=3000,
                    vm_name='Ubuntu-Desktop-24 (GUI)',
                    cores=1,
                    ram=1024,
                    storage=15,
                    guacamole_protocol=GuacamoleConnection.Protocol.RDP,
                    is_lxc=False,
                    is_active=True,
                    node=1
                )
                VMTemplates.objects.create(
                    vm_id=3001,
                    vm_name='Ubuntu-Desktop-22 (GUI)',
                    cores=1,
                    ram=1024,
                    storage=15,
                    guacamole_protocol=GuacamoleConnection.Protocol.RDP,
                    is_lxc=False,
                    is_active=True,
                    node=1,
                )
                VMTemplates.objects.create(
                    vm_id=3000,
                    vm_name='Ubuntu-Server-24 (TUI)',
                    cores=1,
                    ram=1024,
                    storage=15,
                    guacamole_protocol=GuacamoleConnection.Protocol.SSH,
                    is_lxc=False,
                    is_active=True,
                    node=1,
                )
                VMTemplates.objects.create(
                    vm_id=3001,
                    vm_name='Ubuntu-Server-22 (TUI)',
                    cores=1,
                    ram=1024,
                    storage=15,
                    guacamole_protocol=GuacamoleConnection.Protocol.SSH,
                    is_lxc=False,
                    is_active=True,
                    node=1,
                )
                VMTemplates.objects.create(
                    vm_id=4000,
                    vm_name='Ubuntu-LXC-23',
                    cores=1,
                    ram=1024,
                    storage=10,
                    guacamole_protocol=GuacamoleConnection.Protocol.SSH,
                    is_lxc=True,
                    is_active=True,
                    node=1,
                )

        def create_test_data(sender, **kwargs):

            if not RequestEntry.objects.exists():
                
                nodes = Nodes.objects.all()
                templates = VMTemplates.objects.all()
                faculty_users = User.objects.filter(user_type=User.UserType.FACULTY)
                tsg_users = User.objects.filter(user_type=User.UserType.TSG)

                statuses = ['PENDING', 'FOR REVISION', 'PROCESSING', 'ACCEPTED', 'ONGOING', 'COMPLETED', 'DELETED', 'REJECTED']
                use_cases = ['CLASS COURSE', 'RESEARCH', 'THESIS', 'TEST']
                use_case_weights = [0.7, 0.1, 0.1, 0.1]
                course_databank = [
                    'CCICOMP', 'CCINFOM', 'CCPROG1', 'CCPROG2', 'CCPROG3', 'IT-PROG', 'ITSRAQA', 'ITSYSOP',
                    'ITCMSY1', 'ITCMSY2', 'ITISDEV', 'ITDBADM', 'ITSECWB', 'CCAPDEV', 'ITSYSAD', 'ITPLANN',
                    'ITISORG', 'ITSECUR', 'MOBDEVE', 'ITSTRAG', 'ITISPRJ'
                ]

                for _ in range(len(course_databank)):

                    status = choice(statuses)
                    request_date = timezone.localtime() - timedelta(days=randint(1, 7))
                    date_needed = request_date + timedelta(days=randint(3, 10))
                    expiration_date = date_needed + timedelta(days=randint(90, 120)) 
                    rejected_date = request_date + timedelta(days=randint(1, 3)) if status == RequestEntry.Status.REJECTED else None
                    vm_date_tested = None
                    ongoing_date = None
                    expired_date = None

                    if status in [RequestEntry.Status.ACCEPTED, RequestEntry.Status.ONGOING, RequestEntry.Status.COMPLETED, RequestEntry.Status.DELETED]:
                        vm_date_tested = request_date + timedelta(days=randint(1, 3))
                        ongoing_date = vm_date_tested + timedelta(days=randint(1, 3))
                        expired_date = ongoing_date + timedelta(days=randint(90, 120))

                        if expired_date < expiration_date:
                            expired_date = expiration_date + timedelta(days=randint(1, 30))

                    request_entry = RequestEntry.objects.create(
                        ram=randint(4, 32),
                        has_internet=False,
                        status=status,
                        requester=choice(faculty_users),
                        assigned_to=choice(tsg_users) if status != RequestEntry.Status.PENDING else None,
                        template=choice(templates),
                        cores=randint(1, 16),
                        request_date=request_date,
                        date_needed=date_needed,
                        expiration_date=expiration_date,
                        expired_date=expired_date,
                        rejected_date=rejected_date,
                        vm_date_tested=vm_date_tested,
                        ongoing_date=ongoing_date,
                    )

                    use_case = choices(use_cases, weights=use_case_weights, k=1)[0]

                    # CLASS COURSE
                    if use_case == RequestUseCase.UseCase.COURSE:

                        used_courses = RequestUseCase.objects.filter(
                            request__status__in=['PENDING', 'FOR REVISION', 'PROCESSING', 'ACCEPTED', 'ONGOING']
                        ).values_list('request_use_case', flat=True)

                        available_courses = [course for course in course_databank if course not in used_courses]

                        if available_courses:
                            course = choice(available_courses)
                            section = randint(1, 20)
                            node = choice(nodes)
                            for i in range(randint(0, 5)):

                                vm_count = randint(1, 5)

                                RequestUseCase.objects.create(
                                    request_use_case=course,
                                    request=request_entry,
                                    vm_count=vm_count,
                                )
                            
                            vm_ids = generate_vm_ids(request_entry.get_total_no_of_vm())
                            vm_names = generate_vm_names(request_entry)

                            for i in range(len(vm_names)):
                                
                                VirtualMachines.objects.create(
                                    vm_id=vm_ids[i],
                                    vm_name=vm_names[i],
                                    cores=request_entry.cores,
                                    ram=request_entry.ram,
                                    storage=request_entry.template.storage,
                                    ip_add="10.10.10.10",
                                    request=request_entry,
                                    node=node,
                                )

                    # RESEARCH TEST THESIS
                    else:

                        vm_count = randint(1, 5)
                        RequestUseCase.objects.create(
                            request_use_case=use_case,
                            request=request_entry,
                            vm_count=vm_count,
                        )

                        node = choice(nodes)

                        vm_ids = generate_vm_ids(vm_count)
                        vm_names = generate_vm_names(request_entry)

                        for i in range(len(vm_names)):
                            VirtualMachines.objects.create(
                                vm_id=vm_ids[i],
                                vm_name=vm_names[i],
                                cores=request_entry.cores,
                                ram=request_entry.ram,
                                storage=request_entry.template.storage,
                                ip_add="10.10.10.10",
                                request=request_entry,
                                node=node,
                            )

        post_migrate.connect(create_initial_users)
        post_migrate.connect(create_initial_nodes)
        post_migrate.connect(create_initial_vm_templates)
        post_migrate.connect(create_test_data)
