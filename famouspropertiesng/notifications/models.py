from django.db import models

# Create your models here.
class StaffFCMToken(models.Model):
    user = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='fcm_tokens')
    device_id = models.CharField(max_length=255)  # e.g. "chrome-desktop"
    fcm_token = models.CharField(max_length=255)
    platform = models.CharField(max_length=100, null=True, blank=True)  # e.g. "Windows"
    vendor = models.CharField(max_length=100, null=True, blank=True)  # e.g. "Google Inc."
    mobile = models.CharField(max_length=50, null=True, blank=True)  # e.g. "desktop"
    architecture = models.CharField(max_length=50, null=True, blank=True)  # e.g. "x86"
    platformVersion = models.CharField(max_length=50, null=True, blank=True)  # e.g. "10"
    browserName = models.CharField(max_length=100, null=True, blank=True)  # e.g. "Chrome"
    browserVersion = models.CharField(max_length=50, null=True, blank=True)  # e.g. "114.0.5735.199"
    readableSummary = models.CharField(max_length=255, null=True, blank=True)  # e.g. "Chrome on Windows"
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'device_id')  # 👈 one record per user per device

    def __str__(self):
        return f"{self.user.email} - {self.device_id} - {self.fcm_token[:10]}..."