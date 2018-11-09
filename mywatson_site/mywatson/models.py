from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from sorl.thumbnail import ImageField
import os
import json

####################################################################


def user_directory_path(instance, filename):
    # file will be uploaded to MEDIA_ROOT/photos/user_<id>/<filename>
    path = 'photos/{0}/{1}'.format(instance.user, filename)
    return path


FACES_FOLDER = 'faces'


class Photo(models.Model):
    date_created = models.DateTimeField(auto_now_add=True)
    date_modified = models.DateTimeField(auto_now=True)
    image = models.ImageField(upload_to=user_directory_path)
    user = models.ForeignKey(User, null=True, on_delete=models.CASCADE)


class Tag(models.Model):
    tag = models.CharField(max_length=100, default="tag")
    category = models.CharField(max_length=20, default="None")
    score = models.DecimalField(default=1, decimal_places=3, max_digits=6)
    photo = models.ForeignKey(Photo, null=True, on_delete=models.CASCADE)
    startX = models.IntegerField(null=True)
    startY = models.IntegerField(null=True)
    endX = models.IntegerField(null=True)
    endY = models.IntegerField(null=True)


class InvertedIndex(models.Model):
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE)
    photo = models.ForeignKey(Photo, on_delete=models.CASCADE)


class Face(models.Model):
    user = models.ForeignKey(User, null=True, on_delete=models.CASCADE)
    face = models.ImageField(max_length=256)
    photo = models.ForeignKey(Photo, null=True, on_delete=models.CASCADE)
    tag = models.ForeignKey(Tag, null=True, on_delete=models.CASCADE)


class FaceCluster(models.Model):
    n_clusters = models.IntegerField(null=True)
    cluster_id = models.IntegerField(null=True)
    user = models.ForeignKey(User, null=True, on_delete=models.CASCADE)
    face = models.ForeignKey(Face, null=True, on_delete=models.CASCADE)
    name = models.CharField(max_length=50, null=True)
    silhouette_score = models.FloatField(default=0)

    class Meta:
        unique_together = ('n_clusters', 'cluster_id', 'face')


class UserPreferences(models.Model):
    """
    Saves the user preferences like the number of clusters to display
    """
    user = models.ForeignKey(User, null=True, on_delete=models.CASCADE)
    n_clusters = models.IntegerField(null=True)

    class Meta:
        unique_together = ('user', 'n_clusters')

class Features(models.Model):
    face = models.ForeignKey(Face, null=True, on_delete=models.CASCADE)
    feature = models.TextField()

    def set_feature(self, x):
        self.feature = json.dumps(x)

    # def get_feature(self):
    #     return json.loads(self.feature)

    # Although these two functions look the same,
    # the first one cannot return anything other than a string,
    # as it is an attribute getter
    def get_feature_list(self):
        return json.loads(self.feature)
####################################################################
# Signals
####################################################################


@receiver(models.signals.post_delete, sender=Photo)
def auto_delete_file_on_delete(sender, instance, **kwargs):
    """
    Deletes image from filesystem
    when corresponding 'Photo' object is deleted.
    """
    if instance.image:
        if os.path.isfile(instance.image.path):
            try:
                # os.remove(instance.image.path)
                with open('to_remove.txt', 'a', encoding='utf-8') as to_remove:
                    to_remove.write('\n')
                    to_remove.write(instance.image.path)
            except PermissionError as e:
                print("[ERROR] When deleting", instance.image.path)
                print(e)


@receiver(models.signals.pre_save, sender=Photo)
def auto_delete_file_on_change(sender, instance, **kwargs):
    """
    Deletes old file from filesystem
    when corresponding 'Photo' object is updated
    with new file.
    """
    if not instance.pk:
        return False
    try:
        old_file = Photo.objects.get(pk=instance.pk).image
    except Photo.DoesNotExist:
        return False

    new_file = instance.image
    if not old_file == new_file:
        if os.path.isfile(old_file.path):
            os.remove(old_file.path)


@receiver(models.signals.post_delete, sender=Face)
def force_cluster_recompute_on_delete(sender, instance, **kwargs):
    """
    The removal of an image / tag triggers the deletion of the corresponding face / faces.
    Therefore when one of those faces are deleted, ALL the clusters should be recomputed.
    """
    if instance.face:
        FaceCluster.objects.all().delete()


@receiver(models.signals.post_delete, sender=FaceCluster)
def reset_user_preferences_on_cluster_delete(sender, instance, **kwargs):
    """
    The removal of any cluster should cause the user preferences to be reset.
    """
    if instance.user_id:
        UserPreferences.objects.all().delete()
