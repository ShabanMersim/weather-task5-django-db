from django.db import models

class City(models.Model):
    query = models.CharField(max_length=100, unique=True)   # "Sofia,BG"
    name = models.CharField(max_length=100)
    country = models.CharField(max_length=2, blank=True)
    lat = models.FloatField(null=True, blank=True)
    lon = models.FloatField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.query})"


class WeatherSnapshot(models.Model):
    UNITS = (("metric", "metric"), ("imperial", "imperial"))

    city = models.ForeignKey(City, related_name="snapshots", on_delete=models.CASCADE)
    units = models.CharField(max_length=10, choices=UNITS, default="metric")
    temp = models.FloatField()
    humidity = models.IntegerField()
    condition = models.CharField(max_length=100)
    fetched_at = models.DateTimeField(auto_now_add=True, db_index=True)
    raw = models.JSONField(null=True, blank=True)
    source = models.CharField(max_length=20, default="api")  # "random" | "manual" | "api"

    class Meta:
        ordering = ["-fetched_at"]
        indexes = [models.Index(fields=["city", "-fetched_at"])]

    def __str__(self):
        return f"{self.city.name} {self.temp}{'C' if self.units=='metric' else 'F'} @ {self.fetched_at:%Y-%m-%d %H:%M}"
