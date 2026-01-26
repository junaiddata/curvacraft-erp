# Generated migration to rename Subcontractor to Contractor

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('purchase_orders', '0001_initial'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='Subcontractor',
            new_name='Contractor',
        ),
        migrations.RenameField(
            model_name='purchaseorder',
            old_name='subcontractor',
            new_name='contractor',
        ),
    ]
