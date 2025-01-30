from .models import User, Role, UserProfile,MenuPermission,File_Upload,L2_Production,L3_Production,L1_Production
from django.db.models import F, ExpressionWrapper, DurationField, Count, Sum
from django.shortcuts import get_object_or_404, render,redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import check_password
from django.contrib.auth.hashers import make_password
from django.http import HttpResponse, JsonResponse
from datetime import timedelta, timezone
from django.contrib.auth import  login
from django.utils.timezone import now
from django.contrib import messages
from django.db import transaction
from django.utils import timezone 
from django.db.models import Q
from datetime import datetime
from io import StringIO
import pandas as pd
import json
import pytz
import csv


# dashboard
def dashboard(request):
    return render(request, 'dashboard.html')

# Login funciton 
def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        try:
            user = User.objects.get(username=username)
            if check_password(password, user.password):
                if user.user_status == 1 and user.is_active:
                    login(request, user)

                    try:
                        user_profile = UserProfile.objects.get(user=user)
                        request.session['user_role'] = user_profile.role.role_type if user_profile.role else None
                    except UserProfile.DoesNotExist:
                        request.session['user_role'] = None

                    if request.session.get('user_role') != 'Admin':
                        try:
                            menu_permission = MenuPermission.objects.get(user=user)
                            allowed_menus = menu_permission.menu_names.split(',')
                            request.session['allowed_menus'] = [menu.strip() for menu in allowed_menus]
                        except MenuPermission.DoesNotExist:
                            request.session['allowed_menus'] = []
                    else:
                        request.session['allowed_menus'] = ['dashboard', 'user_creation', 'upload', 'menu_permission','l1_production','l2_production','l3_production','production_report']  # Add all menu names for admin

                    if len(request.session['allowed_menus']) == 1:
                        return redirect(request.session['allowed_menus'][0]) 
                    else:
                        return redirect('dashboard') 

                else:
                    messages.error(request, "Your account is inactive or invalid.")
            else:
                messages.error(request, "Incorrect password. Please try again.")
        except User.DoesNotExist:
            messages.error(request, "User with this username does not exist.")

    return render(request, 'login.html')


# create user
@login_required
def user_creation(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        role_type = request.POST.get('role_type')

        if not all([username, first_name, last_name, role_type]):
            messages.error(request, 'All fields except password are required.')
            return redirect('user_creation')

        try:
            if User.objects.filter(username=username, user_status=1).exists():
                messages.error(request, 'Username already exists with active status.')
                return redirect('user_creation')

            # If username exists but has user_status=0, update the existing user and user profile
            existing_user = User.objects.filter(username=username, user_status=0).first()

            if existing_user:
                # Update the existing user's user_status to 1 (active)
                existing_user.first_name = first_name
                existing_user.last_name = last_name
                existing_user.user_status = 1
                existing_user.save()

                # Reactivate the associated user profile
                existing_user_profile = UserProfile.objects.filter(user=existing_user).first()
                if existing_user_profile:
                    existing_user_profile.user_status = 1  # Mark as active
                    existing_user_profile.save()

                messages.success(request, f'User {username} is reactivated and updated successfully!')
                
                user_profiles = UserProfile.objects.filter(
                    user_status=1
                )
                
                return render(request, 'user_creation.html', {'user_profiles': user_profiles})

            # If username doesn't exist or user_status=1, create a new user
            default_password = 'admin123$'
            
            user = User.objects.create(
                username=username,
                first_name=first_name,
                last_name=last_name,
                password=make_password(default_password),
                created_by=request.user,
                user_status=1  
            )

            role = Role.objects.create(
                user=user,
                role_type=role_type,
                created_by=request.user
            )

            UserProfile.objects.create(
                user=user,
                role=role,
                created_by=request.user,
                user_status=1  # Set the profile status to active
            )

            messages.success(request, f'User {username} with role {role_type} created successfully!')

            return redirect('user_creation')

        except Exception as e:
            messages.error(request, f'Error creating user: {e}')
            return redirect('user_creation')

    # Fetch user profiles to display
    user_profiles = UserProfile.objects.filter(
        user_status=1
    ).order_by('id')

    return render(request, 'user_creation.html', {'user_profiles': user_profiles})


# update user
def update_user(request, username):
    if request.method == 'POST':
        try:
            with transaction.atomic():
                user_profile = get_object_or_404(UserProfile, user__username=username)
                user = user_profile.user
                user.first_name = request.POST.get('first_name')
                user.last_name = request.POST.get('last_name')
                user.save()
                print(user, 'User updated successfully')

                role_id = request.POST.get('role_id')  
                role = get_object_or_404(Role, id=role_id)
                role_type = request.POST.get('role_type_edit') 
                role.role_type = role_type 
                role.save()
                print(role, 'Role updated successfully')

                return JsonResponse({'success': True})

        except Exception as e:
            print("Error:", str(e))
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Invalid request method'})


# delete user
def delete_user(request, user_id):
    if request.method == "DELETE":

        user_profile = get_object_or_404(UserProfile, user__id=user_id)
        user = get_object_or_404(User, id=user_id)

        user_profile.user_status = 0 
        user.user_status = 0  

        user_profile.save()
        user.save()

        return JsonResponse({"message": f"User status updated to inactive for user_id {user_id}."}, status=200)
    
    return JsonResponse({"error": "Invalid request method."}, status=400)


# file upload for provide task
def upload(request):
    if request.method == 'POST':
        uploaded_file = request.FILES['file']
        
        # Check for valid file types
        if not (uploaded_file.name.endswith('.csv') or 
                uploaded_file.name.endswith('.xlsx') or 
                uploaded_file.name.endswith('.tsv')):
            messages.error(request, 'File is not CSV, Excel, or TSV type')
            return redirect('upload') 

        try:
            # Read the file into a DataFrame
            if uploaded_file.name.endswith('.csv'):
                data = pd.read_csv(uploaded_file)

            elif uploaded_file.name.endswith('.xlsx'):
                data = pd.read_excel(uploaded_file)

            elif uploaded_file.name.endswith('.tsv'):
                data = pd.read_csv(uploaded_file, sep='\t')  

            # Store each row in the database
            for index, row in data.iterrows():
                File_Upload.objects.create(
                    key_asin=row['key_asin'],
                    candidate_asin=row['candidate_asin'],
                    region=row['region'],
                    created_by=request.user,
                    file_name=uploaded_file.name
                )

            messages.success(request, 'File uploaded successfully and data stored!')
            return redirect('upload')  
        
        except Exception as e:
            messages.error(request, f'Error processing file: {e}')
            return redirect('upload')  

    return render(request, 'upload.html')



# get the formatted menu names function to create menu permission
def format_menu_name(menu_name):
    """Formats menu name: capitalizes first letter and replaces underscores with spaces."""
    print(menu_name)
    return menu_name.replace("_", " ").title()


# create the menu permisison for user
def menu_permission(request):   

    profiles = UserProfile.objects.select_related('user').filter(
        user_status=1, 
        role__role_type__in=['TL', 'TM']
    ).order_by('id')

    print(profiles)

    # Prepare the user data to send to the frontend
    user_data = [
        {
            "id": profile.user.id,
            "username": profile.user.username,
        }
        for profile in profiles
    ]
    
    # Predefined menu items
    menu_items = [
        {'name': 'User Creation', 'url_name': 'user_creation'},
        {'name': 'Upload', 'url_name': 'upload'},
        {'name': 'Menu Permission', 'url_name': 'menu_permission'},
        {'name': 'L1 Production', 'url_name': 'l1_production'},
        {'name': 'L2 Production', 'url_name': 'l2_production'},
        {'name': 'L3 Production', 'url_name': 'l3_production'},
        {'name': 'Production Report', 'url_name': 'production_report'},
        # ... add other menu items here
    ]
    
    # Fetching menu permissions
    permissions = MenuPermission.objects.all().filter(user_status=1).order_by('user_id')
    
    # Initialize the list for formatted permissions
    permissions_data = []

    # Loop over permissions and format the data
    for permission in permissions:
        # Split and format menu names
        formatted_menus = [format_menu_name(menu) for menu in permission.menu_names.split(',')] 
        print(formatted_menus)

        menu_ids = permission.menu_names.split(',') if permission.menu_names else []
              
        # Add the formatted data to the list
        permissions_data.append({
            "id": permission.id,
            "username": permission.user.username,
            "menu_allocated": ", ".join(formatted_menus),
            "created_by": permission.created_by.username,
            "menu_ids": menu_ids,
        })
    
    # Prepare context for the template
    context = {
        "users": user_data,
        "menu_items": menu_items,
        "permissions": permissions_data,  
    }

    # Handle AJAX requests
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({"users": user_data}, status=200)

    # Handle form submission (POST request)
    if request.method == "POST":
        user_ids = request.POST.getlist('user_ids[]')
        menu_names = request.POST.getlist('menu_names[]')
        
        # Create a comma-separated string of menu names
        menu_names_string = ','.join(menu_names)

        for user_id in user_ids:
            try:
                user = User.objects.get(id=user_id) 
                print(user) 
                
                permission = MenuPermission.objects.filter(user=user).first()
                print(permission, 'eeeeeeeeeee')

                if permission and permission.user_status == 0:
                    permission.user_status = 1  
                    permission.save()  
                                    
                permission, created = MenuPermission.objects.get_or_create(
                    user=user,
                    defaults={'menu_names': menu_names_string, 'created_by': request.user}
                ).order_by('id')
                
                if not created:
                    permission.menu_names = menu_names_string
                    permission.save()
            except User.DoesNotExist: 
                print(f"Error: User with ID {user_id} not found.")
               
        
        return redirect('menu_permission')  

    return render(request, 'menu_permission.html', context)



# update the menu permission data for user

@login_required
def update_menu_permission(request, permission_id):
    if request.method == 'POST':
        permission = get_object_or_404(MenuPermission, id=permission_id)

        try:
            data = json.loads(request.body)
            menu_allocated = data.get('menu_allocated')

            if menu_allocated is not None:
                # If it's a list (multiple selected), handle that
                if isinstance(menu_allocated, list):
                    backend_menu_names = []
                    menu_mapping = {
                        'User Creation': 'user_creation',
                        'Upload': 'upload',
                        'Menu Permission': 'menu_permission',
                        'L3 Production': 'l3_production',
                        'L2 Production': 'l2_production',
                        'L1 Production': 'l1_production',
                        'Production Report':'production_report',

                    }

                    for menu_name in menu_allocated:
                        backend_name = menu_mapping.get(menu_name)
                        if backend_name:
                            backend_menu_names.append(backend_name)
                    permission.menu_names = ",".join(backend_menu_names)
                else:
                    permission.menu_names = menu_mapping.get(menu_allocated, "")

                permission.save()

                return JsonResponse({'success': True})

            else:
                return JsonResponse({'success': False, 'error': 'menu_allocated is required'})

        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'Invalid JSON data'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Invalid request method'})


# delete menu permission data
def delete_menu_permission(request, permission_id):
    if request.method == 'POST':
        try:
            permission = get_object_or_404(MenuPermission, id=permission_id)
            permission.user_status = 0  # Set status to inactive
            permission.save()
            return JsonResponse({'success': True})
        except MenuPermission.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Permission not found'}, status=404)
        except Exception as e:  # Catch other potential errors
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=405) # Return 405 for incorrect method


# Format time function
def convert_seconds_to_hhmmss(total_seconds):
    hours, remainder = divmod(int(total_seconds), 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02}:{minutes:02}:{seconds:02}" 

# L1 Production function
@login_required
def l1_production(request):
    context = {}
    key_word = 'Customized'  

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            with transaction.atomic():
                # Fetch completed task stats
                task_stats = L1_Production.objects.filter(
                    asin_master__l1_workstatus='Completed',
                    asin_master__l1_picked_by=request.user
                ).annotate(
                    total_time=ExpressionWrapper(
                        F('end_time') - F('start_time'),
                        output_field=DurationField()
                    )
                ).aggregate(
                    overall_total_time=Sum('total_time'),
                    completed_count=Count('id')
                )

                # Calculate total time and average time per task
                total_time_seconds = (
                    task_stats['overall_total_time'].total_seconds()
                    if task_stats['overall_total_time'] else 0
                )
                completed_count = task_stats['completed_count']
                formatted_time = convert_seconds_to_hhmmss(total_time_seconds)

                avt_total_seconds = total_time_seconds / completed_count if completed_count > 0 else 0
                avt_total = str(timedelta(seconds=int(avt_total_seconds)))

                print(completed_count, formatted_time, total_time_seconds, avt_total, '11111111111')

                # Handling 'Random' keyword
                if key_word == 'Random':
                    current_asin_data = File_Upload.objects.filter(
                        l1_picked_by=request.user,
                        l1_workstatus='Picked'
                    ).first()

                    if current_asin_data:
                        # User is already working on a task
                        context = {
                            "id": current_asin_data.id,
                            "key_asin": current_asin_data.key_asin,
                            "candidate_asin": current_asin_data.candidate_asin,
                            "region": current_asin_data.region,
                            "message": "You are currently working on this ASIN.",
                            "completed_count": completed_count,
                            "avg_time_per_task": avt_total,
                        }
                    else:
                        # Fetch a new task
                        asin_data = File_Upload.objects.select_for_update(skip_locked=True).filter(
                            l2_workstatus='Not Picked',
                            l3_workstatus='Not Picked'
                        ).exclude(
                            id__in=L1_Production.objects.values_list('asin_master_id', flat=True)
                        ).order_by("id").first()

                        if asin_data:
                            # Assign task to user
                            l1_task, created = L1_Production.objects.get_or_create(
                                asin_master=asin_data,
                                created_by=request.user,
                                defaults={"start_time": timezone.now()}
                            )
                            if created:
                                asin_data.l1_workstatus = 'Picked'
                                asin_data.l1_picked_by = request.user
                                asin_data.save()

                            asin_data.l1_production = l1_task
                            asin_data.save()
                            

                            context = {
                                "id": asin_data.id,
                                "key_asin": asin_data.key_asin,
                                "candidate_asin": asin_data.candidate_asin,
                                "region": asin_data.region,
                                "completed_count": completed_count,
                                "avg_time_per_task": avt_total,
                            }
                        else:
                            context = {
                                "message": "No more records available.",
                                "completed_count": completed_count,
                                "avg_time_per_task": avt_total,

                            }

                # Handling 'Customized' keyword
                elif key_word == 'Customized':
                    print(request.user,'sssssss')
                    current_asin_data = File_Upload.objects.filter(
                        l1_picked_by=request.user,
                        l1_workstatus='Picked'
                    ).first()

                    print(current_asin_data)

                    if current_asin_data:
                        # User is already working on a customized task
                        context = {
                            "id": current_asin_data.id,
                            "key_asin": current_asin_data.key_asin,
                            "candidate_asin": current_asin_data.candidate_asin,
                            "region": current_asin_data.region,
                            "message": "You are currently working on this ASIN in L1.",
                            "completed_count": completed_count,
                            "avg_time_per_task": avt_total,
                        }
                    else:
                        current_user_id = request.user

                        excluded_asins = File_Upload.objects.filter(
                            Q(l2_workstatus__in=['Picked', 'Completed']) | 
                            Q(l3_workstatus__in=['Picked', 'Completed']) |
                            (Q(l1_picked_by__isnull=False) & ~Q(l1_picked_by_id=current_user_id))
                        ).values_list('key_asin', flat=True)

                        asin_data = File_Upload.objects.select_for_update(skip_locked=True).filter(
                            l1_workstatus='Not Picked',
                            l1_picked_by__isnull=True
                        ).exclude(key_asin__in=excluded_asins).order_by("id").first()


                        if asin_data:
                            # Assign task to user
                            l1_task, created = L1_Production.objects.get_or_create(
                                asin_master=asin_data,
                                created_by=request.user,
                                defaults={"start_time": timezone.now()}
                            )
                            if created:
                                asin_data.l1_workstatus = 'Picked'
                                asin_data.l1_picked_by = request.user
                                asin_data.save()

                            asin_data.l1_production = l1_task
                            asin_data.save()


                            context = {
                                "id": asin_data.id,
                                "key_asin": asin_data.key_asin,
                                "candidate_asin": asin_data.candidate_asin,
                                "region": asin_data.region,
                                "completed_count": completed_count,
                                "avg_time_per_task": avt_total,
                            }
                        else:
                            context = {
                                "message": "No more records available.",
                                "completed_count": completed_count,
                                "avg_time_per_task": avt_total,

                            }

                return JsonResponse(context)

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    # Render HTML if not an AJAX request
    return render(request, 'l1_production.html', context)


# submit task for l1_production
@login_required
def l1_submit_task(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            print(data,'aaadapfwpv ')
            print("Received data:", data)

            record_id = data.get("id")
            start_time_str = data.get("start_time")  
            l1_workstatus = data.get("work_status") 
            user = request.user 
            que1 = data.get('q1', '').strip()
            que2 = data.get('reason', '').strip()
            que3 = data.get('comment', '').strip()

            # form validation for production
            if not que1 or not que2:
                return JsonResponse({
                    "success": False,
                    "message": "Please fill in all the required fields."
                }, status=400)
            
            print(que1,que2,que3,'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa')

            print(f"Received start_time: {start_time_str}, l1_workstatus: {l1_workstatus}")

            if not record_id or not start_time_str or not l1_workstatus:
                return JsonResponse({"message": "Missing required data (id, start_time, l1_workstatus)"}, status=400)

            try:
                start_time = datetime.fromisoformat(start_time_str.replace("Z", "+00:00"))
                
                if start_time.tzinfo is not None:
                    start_time = start_time.replace(tzinfo=None)

                start_time = timezone.make_aware(start_time)
            except ValueError as e:
                print(f"Error parsing start_time: {e}")
                return JsonResponse({"message": "Invalid start_time format. Ensure it's ISO 8601."}, status=400)

            asin_master = File_Upload.objects.filter(id=record_id).first()
            print(asin_master.id)

            if not asin_master:
                return JsonResponse({"message": "Record not found"}, status=404)
    
            l1_task = L1_Production.objects.filter(asin_master=asin_master, created_by=user).first()

            if not l1_task:
                return JsonResponse({"message": "Task not found in L2_Production"}, status=404)

            # Update the work status based on the button clicked
            asin_master.l1_workstatus = l1_workstatus
            asin_master.save()
            print(asin_master,'id master')

            l1_task.start_time = l1_task.start_time or start_time  
            l1_task.end_time = timezone.now() 
            l1_task.que1 = que1
            l1_task.que2 = que2
            l1_task.que3 = que3
            l1_task.save()
            print("Updated L1_Production:", l1_task)


            if l1_workstatus == 'Completed' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    "message": "Task completed successfully, redirecting to dashboard",
                }, status=200)

            return JsonResponse({
                "message": "Task submitted successfully",
            }, status=200)

        except json.JSONDecodeError:
            return JsonResponse({"message": "Invalid JSON format"}, status=400)
        except Exception as e:
            # Catching unexpected errors
            print(f"Unexpected error: {str(e)}")
            return JsonResponse({"message": f"Error: {str(e)}"}, status=500)

    return JsonResponse({"message": "Invalid request method"}, status=400)



# end of L1 Production

# ----------------- 

# L2 Production


@login_required
def l2_production(request):
    context = {}

    key_word = 'Customized'  # Default value; can be changed dynamically if needed

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            with transaction.atomic():
               
                task_stats = L2_Production.objects.filter(
                    asin_master__l2_workstatus='Completed',
                    asin_master__l2_picked_by=request.user
                ).annotate(
                    total_time=ExpressionWrapper(
                        F('end_time') - F('start_time'),
                        output_field=DurationField()
                    )
                ).aggregate(
                    overall_total_time=Sum('total_time'),
                    completed_count=Count('id')
                )

                # Calculate total time and average time per task
                total_time_seconds = (
                    task_stats['overall_total_time'].total_seconds()
                    if task_stats['overall_total_time'] else 0
                )
                completed_count = task_stats['completed_count']
                formatted_time = convert_seconds_to_hhmmss(total_time_seconds)

                avt_total_seconds = total_time_seconds / completed_count if completed_count > 0 else 0
                avt_total = str(timedelta(seconds=int(avt_total_seconds)))
                
                print(completed_count,formatted_time,total_time_seconds,'11111111111')


                if key_word == 'Random':
                    # Fetch a currently picked task for the user
                    current_asin_data = File_Upload.objects.filter(
                        l2_picked_by=request.user,
                        l2_workstatus='Picked',
                    ).first()

                    if current_asin_data:
                        l2_task, created = L2_Production.objects.get_or_create(
                            asin_master=current_asin_data,
                            created_by=request.user,
                            defaults={"start_time": timezone.now()}
                        )

                        context = {
                            "id": current_asin_data.id,
                            "key_asin": current_asin_data.key_asin,
                            "candidate_asin": current_asin_data.candidate_asin,
                            "region": current_asin_data.region,
                            "message": "You are currently working on this ASIN.",
                            "completed_count": completed_count,
                            "avg_time_per_task": avt_total,
                        }
                    else:
                        # Fetch the first available 'Not Picked' record
                        asin_data = File_Upload.objects.select_for_update(skip_locked=True).filter(
                            l2_workstatus='Not Picked',
                            l3_workstatus='Not Picked',
                            l1_workstatus='Not Picked'
                        ).exclude(
                            id__in=L2_Production.objects.values_list('asin_master_id', flat=True)
                        ).order_by("id").first()

                        if asin_data:
                            print(asin_data)
                            # Assign the record to the logged-in user
                            l2_task, created = L2_Production.objects.get_or_create(
                                asin_master=asin_data,
                                created_by=request.user,
                                defaults={"start_time": timezone.now()}
                            )
                            if created:
                                asin_data.l2_workstatus = 'Picked'
                                asin_data.l2_picked_by = request.user
                                asin_data.save()
                            
                            asin_data.l2_production = l2_task
                            asin_data.save()

                            context = {
                                "id": asin_data.id,
                                "key_asin": asin_data.key_asin,
                                "candidate_asin": asin_data.candidate_asin,
                                "region": asin_data.region,
                                "completed_count": completed_count,
                                "avg_time_per_task": avt_total,
                            }
                        else:
                            context = {
                                "message": "No more records available.",
                                "completed_count": completed_count,
                                "avg_time_per_task": avt_total,

                            }

                elif key_word == 'Customized':
                    # Fetch the current customized task
                    current_asin_data = File_Upload.objects.filter(
                        l2_picked_by=request.user,
                        l2_workstatus='Picked',
                    ).first()

                    if current_asin_data:
                        context = {
                            "id": current_asin_data.id,
                            "key_asin": current_asin_data.key_asin,
                            "candidate_asin": current_asin_data.candidate_asin,
                            "region": current_asin_data.region,
                            "message": "You are currently working on this ASIN.",
                            "completed_count": completed_count,
                            "avg_time_per_task": avt_total,
                        }
                    else:
                        current_user_id = request.user
                        # Fetch a new customized task

                        excluded_asins = File_Upload.objects.filter(
                            Q(l1_workstatus__in=['Picked', 'Completed']) | 
                            Q(l3_workstatus__in=['Picked', 'Completed']) |
                            (Q(l2_picked_by__isnull=False) & ~Q(l2_picked_by_id=current_user_id))
                        ).values_list('key_asin', flat=True)

                        asin_data = File_Upload.objects.select_for_update(skip_locked=True).filter(
                            l2_workstatus='Not Picked',
                            l2_picked_by__isnull=True
                        ).exclude(key_asin__in=excluded_asins).order_by("id").first()


                        if asin_data:
                            # Assign the record to the logged-in user
                            l2_task, created = L2_Production.objects.get_or_create(
                                asin_master=asin_data,
                                created_by=request.user,
                                defaults={"start_time": timezone.now()}
                            )
                            if created:
                                asin_data.l2_workstatus = 'Picked'
                                asin_data.l2_picked_by = request.user
                                asin_data.save()

                            asin_data.l2_production = l2_task
                            asin_data.save()

                            context = {
                                "id": asin_data.id,
                                "key_asin": asin_data.key_asin,
                                "candidate_asin": asin_data.candidate_asin,
                                "region": asin_data.region,
                                "completed_count": completed_count,
                                "avg_time_per_task": avt_total,
                            }
                        else:
                            context = {
                                "message": "No more records available.",
                                "completed_count": completed_count,
                                "avg_time_per_task": avt_total,

                            }
                        return JsonResponse(context)
                    
                return JsonResponse(context)

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    # Render HTML if not an AJAX request
    return render(request, 'l2_production.html', context)




# submit task for l2_production
@login_required
def l2_submit_task(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            print(data,'aaadapfwpv ')
            print("Received data:", data)

            record_id = data.get("id")
            start_time_str = data.get("start_time")  
            l2_workstatus = data.get("work_status") 
            user = request.user 
            que1 = data.get('q1', '').strip()
            que2 = data.get('reason', '').strip()
            que3 = data.get('comment', '').strip()

            # form validation for production
            if not que1 or not que2:
                return JsonResponse({
                    "success": False,
                    "message": "Please fill in all the required fields."
                }, status=400)
            
            print(que1,que2,que3,'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa')

            print(f"Received start_time: {start_time_str}, l2_workstatus: {l2_workstatus}")

            if not record_id or not start_time_str or not l2_workstatus:
                return JsonResponse({"message": "Missing required data (id, start_time, l2_workstatus)"}, status=400)

            try:
                start_time = datetime.fromisoformat(start_time_str.replace("Z", "+00:00"))
                
                if start_time.tzinfo is not None:
                    start_time = start_time.replace(tzinfo=None)

                start_time = timezone.make_aware(start_time)
            except ValueError as e:
                print(f"Error parsing start_time: {e}")
                return JsonResponse({"message": "Invalid start_time format. Ensure it's ISO 8601."}, status=400)

            asin_master = File_Upload.objects.filter(id=record_id).first()
            print(asin_master.id)

            if not asin_master:
                return JsonResponse({"message": "Record not found"}, status=404)

            l2_task = L2_Production.objects.filter(asin_master=asin_master,  created_by=user).first()

            if not l2_task:
                return JsonResponse({"message": "Task not found in L2_Production"}, status=404)

            # Update the work status based on the button clicked
            asin_master.l2_workstatus = l2_workstatus
            asin_master.save()
            print(asin_master,'id master')

            l2_task.start_time = l2_task.start_time or start_time  # Keep the existing start_time if it exists
            l2_task.end_time = timezone.now()  # Update end_time to now
            l2_task.que1 = que1
            l2_task.que2 = que2
            l2_task.que3 = que3
            l2_task.save()
            print("Updated L2_Production:", l2_task)


            if l2_workstatus == 'Completed' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    "message": "Task completed successfully, redirecting to dashboard",

                }, status=200)

            return JsonResponse({
                "message": "Task submitted successfully",
            }, status=200)

        except json.JSONDecodeError:
            return JsonResponse({"message": "Invalid JSON format"}, status=400)
        except Exception as e:
            # Catching unexpected errors
            print(f"Unexpected error: {str(e)}")
            return JsonResponse({"message": f"Error: {str(e)}"}, status=500)

    return JsonResponse({"message": "Invalid request method"}, status=400)


# end of L2 Production
# -----------------
# L3 Production

@login_required
def l3_production(request):
    context = {}
    key_word = 'Customized'  

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            with transaction.atomic():
                # Fetch completed task stats
                
                task_stats = L3_Production.objects.filter(
                    asin_master__l3_workstatus='Completed',
                    asin_master__l3_picked_by=request.user
                ).annotate(
                    total_time=ExpressionWrapper(
                        F('end_time') - F('start_time'),
                        output_field=DurationField()
                    )
                ).aggregate(
                    overall_total_time=Sum('total_time'),
                    completed_count=Count('id')
                )

                # Calculate total time and average time per task
                total_time_seconds = (
                    task_stats['overall_total_time'].total_seconds()
                    if task_stats['overall_total_time'] else 0
                )
                completed_count = task_stats['completed_count']
                formatted_time = convert_seconds_to_hhmmss(total_time_seconds)

                avt_total_seconds = total_time_seconds / completed_count if completed_count > 0 else 0
                avt_total = str(timedelta(seconds=int(avt_total_seconds)))

                print(completed_count,formatted_time,total_time_seconds,'11111111111')

                # Handling 'Random' keyword
                if key_word == 'Random':
                    current_asin_data = File_Upload.objects.filter(
                        l3_picked_by=request.user,
                        l3_workstatus='Picked'
                    ).first()

                    if current_asin_data:
                        # User is already working on a task
                        context = {
                            "id": current_asin_data.id,
                            "key_asin": current_asin_data.key_asin,
                            "candidate_asin": current_asin_data.candidate_asin,
                            "region": current_asin_data.region,
                            "message": "You are currently working on this ASIN.",
                            "completed_count": completed_count,
                            "avg_time_per_task": avt_total,
                        }
                    else:
                        # Fetch a new task
                        asin_data = File_Upload.objects.select_for_update(skip_locked=True).filter(
                            l3_workstatus='Not Picked',
                            l2_workstatus='Not Picked',
                            l1_workstatus='Not Picked'
                        ).exclude(
                            id__in=L3_Production.objects.values_list('asin_master_id', flat=True)
                        ).order_by("id").first()

                        if asin_data:
                            # Assign task to user
                            l3_task, created = L3_Production.objects.get_or_create(
                                asin_master=asin_data,
                                created_by=request.user,
                                defaults={"start_time": timezone.now()}
                            )
                            if created:
                                asin_data.l3_workstatus = 'Picked'
                                asin_data.l3_picked_by = request.user
                                asin_data.save()

                            asin_data.l3_production = l3_task
                            asin_data.save()

                            context = {
                                "id": asin_data.id,
                                "key_asin": asin_data.key_asin,
                                "candidate_asin": asin_data.candidate_asin,
                                "region": asin_data.region,
                                "completed_count": completed_count,
                                "avg_time_per_task": avt_total,
                            }
                        else:
                            context = {
                                "message": "No more records available.",
                                "completed_count": completed_count,
                                "avg_time_per_task": avt_total,

                            }

                # Handling 'Customized' keyword
                elif key_word == 'Customized':
                    current_asin_data = File_Upload.objects.filter(
                        l3_picked_by=request.user,
                        l3_workstatus='Picked'
                    ).first()
                    
                    print(current_asin_data,'aaaa')

                    if current_asin_data:
                        # User is already working on a customized task
                        context = {
                            "id": current_asin_data.id,
                            "key_asin": current_asin_data.key_asin,
                            "candidate_asin": current_asin_data.candidate_asin,
                            "region": current_asin_data.region,
                            "message": "You are currently working on this ASIN in L3.",
                            "completed_count": completed_count,
                            "avg_time_per_task": avt_total,
                        }
                    else:
                        current_user_id = request.user

                        excluded_asins = File_Upload.objects.filter(
                            Q(l1_workstatus__in=['Picked', 'Completed']) | 
                            Q(l2_workstatus__in=['Picked', 'Completed']) |
                            (Q(l3_picked_by__isnull=False) & ~Q(l3_picked_by_id=current_user_id))
                        ).values_list('key_asin', flat=True)

                        asin_data = File_Upload.objects.select_for_update(skip_locked=True).filter(
                            l3_workstatus='Not Picked',
                            l3_picked_by__isnull=True
                        ).exclude(key_asin__in=excluded_asins).order_by("id").first()

                        if asin_data:
                            # Assign task to user
                            l3_task, created = L3_Production.objects.get_or_create(
                                asin_master=asin_data,
                                created_by=request.user,
                                defaults={"start_time": timezone.now()}
                            )
                            if created:
                                asin_data.l3_workstatus = 'Picked'
                                asin_data.l3_picked_by = request.user
                                asin_data.save()

                            asin_data.l3_production = l3_task
                            asin_data.save()

                            context = {
                                "id": asin_data.id,
                                "key_asin": asin_data.key_asin,
                                "candidate_asin": asin_data.candidate_asin,
                                "region": asin_data.region,
                                "completed_count": completed_count,
                                "avg_time_per_task": avt_total,
                            }
                        else:
                            context = {
                                "message": "No more records available.",
                                "completed_count": completed_count,
                                "avg_time_per_task": avt_total,
                            }

                return JsonResponse(context)

        except Exception as e:
            return JsonResponse({'success': False, 'errorqrewef': str(e)})

    # Render HTML if not an AJAX request
    return render(request, 'l3_production.html', context)

# submit task for l3_production
@login_required
def l3_submit_task(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            print(data,'aaadapfwpv ')
            print("Received data:", data)

            record_id = data.get("id")
            start_time_str = data.get("start_time")  
            l3_workstatus = data.get("work_status")  
            user = request.user
            que1 = data.get('q1', '').strip()
            que2 = data.get('reason', '').strip()
            que3 = data.get('comment', '').strip()

            # form validation for production
            if not que1 or not que2:
                return JsonResponse({
                    "success": False,
                    "message": "Please fill in all the required fields."
                }, status=400)
            
            print(que1,que2,que3,'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa')

            print(f"Received start_time: {start_time_str}, l3_workstatus: {l3_workstatus}")

            if not record_id or not start_time_str or not l3_workstatus:
                return JsonResponse({"message": "Missing required data (id, start_time, l3_workstatus)"}, status=400)

            try:
                start_time = datetime.fromisoformat(start_time_str.replace("Z", "+00:00"))
                
                if start_time.tzinfo is not None:
                    start_time = start_time.replace(tzinfo=None)

                start_time = timezone.make_aware(start_time)
            except ValueError as e:
                print(f"Error parsing start_time: {e}")
                return JsonResponse({"message": "Invalid start_time format. Ensure it's ISO 8601."}, status=400)

            asin_master = File_Upload.objects.filter(id=record_id).first()
            print(asin_master.id)

            if not asin_master:
                return JsonResponse({"message": "Record not found"}, status=404)

            l3_task = L3_Production.objects.filter(asin_master=asin_master, created_by=user).first()

            if not l3_task:
                return JsonResponse({"message": "Task not found in L3_Production"}, status=404)

            # Update the work status based on the button clicked
            asin_master.l3_workstatus = l3_workstatus
            asin_master.save()
            print(asin_master,'id master')

            l3_task.start_time = l3_task.start_time or start_time  # Keep the existing start_time if it exists
            l3_task.end_time = timezone.now()  # Update end_time to now
            l3_task.que1 = que1
            l3_task.que2 = que2
            l3_task.que3 = que3
            l3_task.save()
            print("Updated L3_Production:", l3_task)

            if l3_workstatus == 'Completed' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    "message": "Task completed successfully, redirecting to dashboard",

                }, status=200)

            return JsonResponse({
                "message": "Task submitted successfully",
            }, status=200)

        except json.JSONDecodeError:
            return JsonResponse({"message": "Invalid JSON format"}, status=400)
        except Exception as e:
            # Catching unexpected errors
            print(f"Unexpected error: {str(e)}")
            return JsonResponse({"message": f"Error: {str(e)}"}, status=500)

    return JsonResponse({"message": "Invalid request method"}, status=400)
# end of L3 Production



# Production report with download option function

def convert_to_ist(utc_dt):
    ist = pytz.timezone('Asia/Kolkata')
    if utc_dt and isinstance(utc_dt, datetime):  
        ist_dt = utc_dt.astimezone(ist)  
        return ist_dt.strftime("%Y-%m-%d %H:%M:%S")  
    return ""  

def calculate_time_difference(start_time, end_time):
    if start_time and end_time:
        start_ist = datetime.strptime(convert_to_ist(start_time), "%Y-%m-%d %H:%M:%S")
        end_ist = datetime.strptime(convert_to_ist(end_time), "%Y-%m-%d %H:%M:%S")
        time_diff = end_ist - start_ist  # Get timedelta object

        # Convert timedelta to hours, minutes, and seconds
        hours, remainder = divmod(time_diff.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours:02}:{minutes:02}:{seconds:02}"  # Format as HH:MM:SS
    return ""

def production_report(request):
    file_names = File_Upload.objects.values_list('file_name', flat=True).distinct()
    records = []
    show_download_button = False 

    if request.method == "POST":  
        from_time = request.POST.get("from_time") 
        to_time = request.POST.get("to_time")      
        filename = request.POST.get("filename")
        action = request.POST.get("action")
        
        if from_time and to_time:
            from_datetime = datetime.strptime(from_time, "%Y-%m-%dT%H:%M")
            to_datetime = datetime.strptime(to_time, "%Y-%m-%dT%H:%M")

            from_datetime = timezone.make_aware(from_datetime, timezone.get_current_timezone())
            to_datetime = timezone.make_aware(to_datetime, timezone.get_current_timezone())

            query = File_Upload.objects.filter(
                Q(file_name=filename) & (
                    Q(l1_workstatus='Completed', l1_production__end_time__range=(from_datetime, to_datetime)) |
                    Q(l2_workstatus='Completed', l2_production__end_time__range=(from_datetime, to_datetime))|
                    Q(l3_workstatus='Completed', l3_production__end_time__range=(from_datetime, to_datetime))
                )
            ).select_related('l1_production','l2_production', 'l1_picked_by','l1_picked_by').values(
                'key_asin', 'candidate_asin', 'region', 'created_at', 'created_by', 'file_name',

                'l1_production__start_time', 'l1_production__end_time', 'l1_production__que1',
                'l1_production__que2', 'l1_production__que3','l1_production__created_at',
                
                'l1_picked_by__first_name', 'l1_picked_by__last_name', 'l1_picked_by__username',

                'l2_production__start_time', 'l2_production__end_time', 'l2_production__que1',
                'l2_production__que2', 'l2_production__que3','l2_production__created_at',

                'l2_picked_by__first_name', 'l2_picked_by__last_name', 'l2_picked_by__username',

                'l3_production__start_time', 'l3_production__end_time', 'l3_production__que1',
                'l3_production__que2', 'l3_production__que3','l3_production__created_at',

                'l3_picked_by__first_name', 'l3_picked_by__last_name', 'l3_picked_by__username',
            )
    
            records = list(query)

            if action == "view":
                show_download_button = True
                
                return render(request, 'production_report.html', {"records": records, "file_names": file_names, 'show_download_button': show_download_button})

            elif action == "download":
            
                header = [
                        'key ASIN', 'Locale', 'Candidate ASIN', 'DA1-Are candidate_asin & key_asin same?', 
                        'DA1-Reason', 'DA1-Comments', 'User Name', 'Emp ID', 'Start time', 'End time', 
                        'Total Time', 'Production Date', 'DA2-Are candidate_asin & key_asin same?', 
                        'DA2-Reason', 'DA2-Comments', 'User Name', 'Emp ID', 'Start time', 'End time', 
                        'Total Time', 'Production Date', 'DA3-Are candidate_asin & key_asin same?', 
                        'DA3-Reason', 'DA3-Comments', 'User Name', 'Emp ID', 'Start time', 'End time', 
                        'Total Time', 'Production Date'
                    ]

                output = StringIO()
                writer = csv.writer(output)
                
                # Write the header to the CSV
                writer.writerow(header)
        
                for record in records:
                    row = [
                        record['key_asin'], 
                        record['region'], 
                        record['candidate_asin'],
                        # l1 production
                        record.get('l1_production__que1', ""), 
                        record.get('l1_production__que2', ""), 
                        record.get('l1_production__que3', ""),
                        f"{record.get('l1_picked_by__first_name', '')} {record.get('l1_picked_by__last_name', '')}".strip() if record.get('l1_picked_by__first_name') else "",
                        record.get('l1_picked_by__username', ""),
                        convert_to_ist(record.get('l1_production__start_time', None)).split(" ")[1] if record.get('l1_production__start_time') else "",
                        convert_to_ist(record.get('l1_production__end_time', None)).split(" ")[1] if record.get('l1_production__end_time') else "",
                        calculate_time_difference(record.get('l1_production__start_time'), record.get('l1_production__end_time')),
                        record.get('l1_production__created_at', "").date() if isinstance(record.get('l1_production__created_at'), datetime) else "",

                        #l2 production 
                        record.get('l2_production__que1', ""), 
                        record.get('l2_production__que2', ""), 
                        record.get('l2_production__que3', ""),
                        f"{record.get('l2_picked_by__first_name', '')} {record.get('l2_picked_by__last_name', '')}".strip() if record.get('l2_picked_by__first_name') else "",
                        record.get('l2_picked_by__username', ""),
                        convert_to_ist(record.get('l2_production__start_time', None)).split(" ")[1] if record.get('l2_production__start_time') else "",
                        convert_to_ist(record.get('l2_production__end_time', None)).split(" ")[1] if record.get('l2_production__end_time') else "",
                        calculate_time_difference(record.get('l2_production__start_time'), record.get('l2_production__end_time')),
                        record.get('l2_production__created_at', "").date() if isinstance(record.get('l2_production__created_at'), datetime) else "",


                        #l3 production 
                        record.get('l3_production__que1', ""), 
                        record.get('l3_production__que2', ""), 
                        record.get('l3_production__que3', ""),
                        f"{record.get('l3_picked_by__first_name', '')} {record.get('l3_picked_by__last_name', '')}".strip() if record.get('l3_picked_by__first_name') else "",
                        record.get('l3_picked_by__username', ""),
                        convert_to_ist(record.get('l3_production__start_time', None)).split(" ")[1] if record.get('l3_production__start_time') else "",
                        convert_to_ist(record.get('l3_production__end_time', None)).split(" ")[1] if record.get('l3_production__end_time') else "",
                        calculate_time_difference(record.get('l3_production__start_time'), record.get('l3_production__end_time')),
                        record.get('l3_production__created_at', "").date() if isinstance(record.get('l3_production__created_at'), datetime) else "",
                    ]
                                        
                    writer.writerow(row)

                response = HttpResponse(content_type='application/vnd.ms-excel')
                response['Content-Disposition'] = 'attachment; filename="production_report.csv"'

                output.seek(0)
                response.write(output.getvalue())

                # Clean up
                output.close()

                return response
            
    return render(request, 'production_report.html', {"records": records, "file_names": file_names, 'show_download_button': show_download_button})



@login_required
def production_result(request, level="l1"):
    user = request.user

    # Define the filters dynamically based on the level
    level_workstatus = f"{level}_workstatus"
    level_production = f"{level}_production"
    level_picked_by = f"{level}_picked_by"

    production_data = File_Upload.objects.filter(
        **{level_picked_by: user, level_workstatus: "Completed"}
    ).select_related(level_production, level_picked_by)

    first_completed = production_data.order_by("id").first()

    last_completed = production_data.order_by("-id").first()

    context = {
        "production_data": [],
        "level": level,
    }

    if first_completed and last_completed:
        start_production = getattr(first_completed, level_production, None)
        end_production = getattr(last_completed, level_production, None)
        picked_by = getattr(first_completed, level_picked_by, None)

        start_time = timezone.localtime(start_production.start_time) if start_production and start_production.start_time else None
        end_time = timezone.localtime(end_production.end_time) if end_production and end_production.end_time else None

        formatted_start_time = start_time.strftime("%H:%M:%S") if start_time else "N/A"
        formatted_end_time = end_time.strftime("%H:%M:%S") if end_time else "N/A"


        avt_total_time = timedelta(seconds=0)
        completed_count = 0

        for record in production_data:
            production = getattr(record, level_production, None)
            if production and production.start_time and production.end_time:
                start_time = timezone.localtime(production.start_time)
                end_time = timezone.localtime(production.end_time)
                time_diff = end_time - start_time
                print(time_diff)
                avt_total_time += time_diff
                print(avt_total_time)
                completed_count += 1
                avt_final = avt_total_time / completed_count
                # convert without millisec
                avt_task = str(timedelta(seconds=int(avt_final.total_seconds())))
                avt_total_time_str = str(timedelta(seconds=int(avt_total_time.total_seconds())))

        context["production_data"].append({
            "emp_id": picked_by.username if picked_by else "N/A",
            "username": f"{picked_by.first_name} {picked_by.last_name}" if picked_by else "N/A",
            "start_time": formatted_start_time,
            "end_time": formatted_end_time,
            "total_time": avt_total_time_str,
            "region": first_completed.region if first_completed else "N/A",
            "production_date": timezone.localtime(first_completed.created_at).date() if isinstance(first_completed.created_at, datetime) else "",
            "avt": avt_task,
            "completed_count" : completed_count
        })

    return render(request, "production_result.html", context)

