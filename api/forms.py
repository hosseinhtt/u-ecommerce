# forms.py
from django import forms

class AddToCartForm(forms.Form):
    product_id = forms.IntegerField()
    variation_category = forms.CharField(required=False)  # Add this field for variation category
    variation_value = forms.CharField(required=False)     # Add this field for variation value

    def clean(self):
        cleaned_data = super().clean()
        variation_category = cleaned_data.get("variation_category")
        variation_value = cleaned_data.get("variation_value")

        # Check if both variation_category and variation_value are provided or none at all
        if (variation_category and not variation_value) or (variation_value and not variation_category):
            raise forms.ValidationError("Both variation_category and variation_value are required together or none at all.")

        return cleaned_data
