from django.db import models
from django.contrib.auth.models import AbstractUser

# Create your models here.
class User(AbstractUser):
	# middle_name = models.CharField(max_length=100, null=True, blank=True)
	email = models.EmailField(max_length=200, unique=True)
	mobile_no = models.CharField(max_length=20)
	address = models.CharField(max_length=200)

	# location fields
	# city
	city = models.CharField(max_length=100, null=True, blank=True)
	cityId = models.IntegerField(null=True, blank=True)
	# state
	state = models.CharField(max_length=100, null=True, blank=True)
	stateId = models.IntegerField(null=True, blank=True)
	# country
	country = models.CharField(max_length=100, null=True, blank=True)
	countryId = models.IntegerField(null=True, blank=True)

	# profile picture fields
	image_url = models.URLField(blank=True, null=True)  # only store ImageKit URL
	fileId = models.CharField(max_length=200, null=True, blank=True)  # store ImageKit fileId

	nearest_bus_stop = models.CharField(max_length=200, null=True, blank=True)
	phoneCode = models.CharField(max_length=10, null=True, blank=True)
	stateCode = models.CharField(max_length=10, null=True, blank=True)
	username = models.CharField(max_length=30, null=True, blank=True)
	password = models.CharField(max_length=128, null=True, blank=True)
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
