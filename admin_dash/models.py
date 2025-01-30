from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings

class User(AbstractUser):

    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, related_name='users_created')
    user_status = models.IntegerField(default=1) 
    
    def __str__(self):
        return self.username
    

class Role(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='roles')
    role_type = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, related_name='role_creators')

    class Meta:
        unique_together = ('user', 'role_type')

    def __str__(self):
        return f"{self.user.username} - {self.role_type}"
    

class UserProfile(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='user_profiles')
    role = models.ForeignKey('Role', on_delete=models.SET_NULL, null=True, related_name='user_profiles')
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, related_name='user_profiles_created_by')
    user_status = models.IntegerField(default=1) 

    def __str__(self):
        return f"{self.user.username} - {self.user.first_name} {self.user.last_name} - {self.role.role_type if self.role else 'No Role'}"



class MenuPermission(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="user_menu_permissions")
    menu_names = models.CharField(max_length=1024)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, related_name="menu_permission_created_by")
    user_status = models.IntegerField(default=1) 
    def __str__(self):
        return f"{self.user.username} - {self.menu_names}"
    

# class AsinData(models.Model):
#     key_asin = models.CharField(max_length=255)
#     candidate_asin = models.CharField(max_length=255)
#     region = models.CharField(max_length=255)
#     created_at = models.DateTimeField(auto_now_add=True) 
#     created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, related_name="asin_data_created_by")  
#     file_name = models.CharField(max_length=255, null=True, blank=True) 
#     workstatus = models.CharField(max_length=50, default='Not Picked') 
#     picked_by = models.ForeignKey(
#         settings.AUTH_USER_MODEL, 
#         on_delete=models.SET_NULL, 
#         null=True, 
#         related_name="asin_data_picked_by"
#     )  
#     task_assign = models.ForeignKey(
#         'TaskAssign', 
#         on_delete=models.CASCADE,
#         null=True,
#         blank=True,
#         related_name="related_asin_data"
#     )
#     def __str__(self):
#         return f"ASIN: {self.key_asin} - Customer ASIN: {self.candidate_asin}"
    
#     start_time = models.DateTimeField(null=True, blank=True)  
#     end_time = models.DateTimeField(null=True, blank=True)
#     q1 = models.CharField(null=True,max_length=255)
#     reason = models.CharField(null=True,max_length=255)
#     comment = models.CharField(null=True,max_length=255)
#     created_at = models.DateTimeField(auto_now_add=True) 
#     created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, related_name="tasks_created_by")  

   
# class TaskAssign(models.Model):
#     asin_data = models.ForeignKey(AsinData, on_delete=models.CASCADE, related_name="task_assigns") 
#     task_customer = models.ForeignKey(AsinData, on_delete=models.CASCADE, related_name="task_customer_assignments", null=True, blank=True) 
#     region = models.ForeignKey(AsinData, on_delete=models.CASCADE, related_name="region_assignments", null=True, blank=True) 
#     start_time = models.DateTimeField(null=True, blank=True)
#     end_time = models.DateTimeField(null=True, blank=True)
#     q1 = models.CharField(null=True,max_length=255)
#     reason = models.CharField(null=True,max_length=255)
#     comment = models.CharField(null=True,max_length=255)
#     created_at = models.DateTimeField(auto_now_add=True) 
#     created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, related_name="tasks_created_by")  

class File_Upload(models.Model):
    key_asin = models.CharField(max_length=255)
    candidate_asin = models.CharField(max_length=255)
    region = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True) 
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, related_name="task_created_by")  
    file_name = models.CharField(max_length=255, null=True, blank=True) 
    
    l3_workstatus = models.CharField(max_length=50, default='Not Picked')
    l3_production = models.ForeignKey(
        'L3_Production', 
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="related_l3_data"
    )

    l2_workstatus = models.CharField(max_length=50, default='Not Picked') 
    l2_production = models.ForeignKey(
        'L2_Production', 
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="related_l2_data"
    )

    l1_workstatus = models.CharField(max_length=50, default='Not Picked') 
    l1_production = models.ForeignKey(
        'L1_Production', 
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="related_l1_data"
    )

    l1_picked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name="l1_picked_by"
    )  
    
    l2_picked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name="l2_picked_by"
    )  
    
    l3_picked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name="l3_picked_by"
    )  
    
    def __str__(self):
        return f"ASIN: {self.key_asin} - Candidate ASIN: {self.candidate_asin}"
    
    
class L3_Production(models.Model):
    asin_master = models.ForeignKey(File_Upload, on_delete=models.CASCADE, related_name="asin_master_id") 
    start_time = models.DateTimeField(null=True, blank=True)  
    end_time = models.DateTimeField(null=True, blank=True)
    que1 = models.CharField(null=True,max_length=255)
    que2 = models.CharField(null=True,max_length=255)
    que3 = models.CharField(null=True,max_length=255)
    created_at = models.DateTimeField(auto_now_add=True) 
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, related_name="l3_created_by")  

    def __str__(self):
        return f"Task for ASIN Data: {self.asin_master.key_asin}"


class L2_Production(models.Model):
    asin_master = models.ForeignKey(File_Upload, on_delete=models.CASCADE, related_name="asin_master_l2") 
    start_time = models.DateTimeField(null=True, blank=True)  
    end_time = models.DateTimeField(null=True, blank=True)
    que1 = models.CharField(null=True,max_length=255)
    que2 = models.CharField(null=True,max_length=255)
    que3 = models.CharField(null=True,max_length=255)
    created_at = models.DateTimeField(auto_now_add=True) 
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, related_name="l2_created_by")  

    def __str__(self):
        return f"Task for ASIN Data: {self.asin_master.key_asin}"


class L1_Production(models.Model):
    asin_master = models.ForeignKey(File_Upload, on_delete=models.CASCADE, related_name="asin_master_l1") 
    start_time = models.DateTimeField(null=True, blank=True)  
    end_time = models.DateTimeField(null=True, blank=True)
    que1 = models.CharField(null=True,max_length=255)
    que2 = models.CharField(null=True,max_length=255)
    que3 = models.CharField(null=True,max_length=255)
    created_at = models.DateTimeField(auto_now_add=True) 
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, related_name="l1_created_by")  

    def __str__(self):
        return f"Task for ASIN Data: {self.asin_master.key_asin}"



