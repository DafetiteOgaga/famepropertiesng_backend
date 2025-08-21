from django.db import models
from django.contrib.auth.models import AbstractUser

# Create your models here.
class User(AbstractUser):
	middle_name = models.CharField(max_length=100, null=True, blank=True)
	email = models.EmailField(max_length=200, unique=True)
	phone = models.CharField(max_length=20)
	# wphone = models.CharField(max_length=15)
	address = models.CharField(max_length=200)
	username = models.CharField(max_length=30, unique=True)
	password = models.CharField(max_length=128, null=True, blank=True)
	# gender = models.CharField(max_length=50, null=True, blank=True)
	# dob = models.DateField(null=True, blank=True)
	# role = models.CharField(max_length=500, null=True, blank=True)
	## region =  models.ForeignKey(Region, on_delete=models.PROTECT, null=True, blank=True)
	# state = models.ForeignKey(State, on_delete=models.PROTECT, blank=True, null=True)
	# location = models.ForeignKey(Location, on_delete=models.PROTECT, blank=True, null=True)
	# deliveries = models.IntegerField(default=0)
	# pendings = models.IntegerField(default=0)
	# profile_picture = models.ImageField(upload_to=unique_profile_pic, null=True, blank=True)
	# aboutme = models.TextField(null=True, blank=True)
	is_deleted = models.BooleanField(default=False)
	class Meta:
		ordering = ['id']


	USERNAME_FIELD = 'email'
	REQUIRED_FIELDS = []
	def __str__(self):
		return f'userObj: {self.email}' # ({self.first_name}) - {self.role} for {self.location} in {self.region}' if self.first_name else self.email

	def delete(self):
		self.is_deleted = True
		self.save()

	# def save(self, *args, **kwargs):
	# 	print('entering save method ###### 1')
	# 	is_new = self.pk is None  # Check if this is a new object
	# 	profile_picture_new_or_updated = False
	# 	msg = None

	# 	# for profile picture
	# 	# Handle new user
	# 	if is_new:
	# 		if self.profile_picture:
	# 			profile_picture_new_or_updated = True
	# 			msg = 'profile_picture_new'
	# 		else:
	# 			# Use default image if no profile picture provided
	# 			profile_picture_new_or_updated = True
	# 			msg = 'profile_picture_default'
	# 	else:
	# 		# Handle existing user
	# 		old_picture = User.objects.get(pk=self.pk).profile_picture
	# 		profile_picture_new_or_updated = old_picture != self.profile_picture
	# 		if profile_picture_new_or_updated:
	# 			msg = 'profile_picture_updated'

	# 	print(f'{msg}: {profile_picture_new_or_updated}')

	# 	if profile_picture_new_or_updated:
	# 		print(f'processing {msg}')
	# 		if self.profile_picture and hasattr(self.profile_picture, 'file'):
	# 			# Process the uploaded file if it exists
	# 			img = Image.open(self.profile_picture)
	# 			if img.mode != 'RGB':
	# 				img = img.convert('RGB')

	# 			min_dim = min(img.width, img.height)
	# 			left = (img.width - min_dim) / 2
	# 			top = (img.height - min_dim) / 2
	# 			right = (img.width + min_dim) / 2
	# 			bottom = (img.height + min_dim) / 2
	# 			img = img.crop((left, top, right, bottom))
	# 			target_size = (200, 200)
	# 			img = img.resize(target_size, Image.LANCZOS)

	# 			print('copying company logo')
	# 			logo_path = os.path.join(settings.MEDIA_ROOT, 'profile_pictures/placeholder.png')
	# 			logo = Image.open(logo_path)
	# 			logo_size = (50, 20)
	# 			logo = logo.resize(logo_size, Image.LANCZOS)
	# 			logo_position = (img.width - logo_size[0] - 10, img.height - logo_size[1] - 10)
	# 			print('pasting company logo')
	# 			img.paste(logo, logo_position, logo)

	# 			output = io.BytesIO()
	# 			img.save(output, format='JPEG', quality=100)
	# 			output.seek(0)

	# 			self.profile_picture = InMemoryUploadedFile(
	# 				output, 'ImageField',
	# 				f"{unique_profile_pic(self, self.profile_picture.name)}",
	# 				'image/jpeg',
	# 				output.getbuffer().nbytes,
	# 				None
	# 			)
	# 		else:
	# 			# Use default placeholder image if no file is provided
	# 			placeholder_path = os.path.join(settings.MEDIA_ROOT, 'profile_pictures/placeholder.png')
	# 			img = Image.open(placeholder_path)
	# 			output = io.BytesIO()
	# 			img.save(output, format='PNG')
	# 			output.seek(0)
	# 			self.profile_picture = InMemoryUploadedFile(
	# 				output, 'ImageField',
	# 				f"{unique_profile_pic(self, 'default_profile.png')}",
	# 				'image/png',
	# 				output.getbuffer().nbytes,
	# 				None
	# 			)
	# 	super().save(*args, **kwargs)
