# Two small view mixins that keep ownership rules in one place: one narrows a
# queryset down to the logged-in user's rows, the other stamps new rows with
# the user who created them.
class OwnerScopedMixin:
    owner_lookup = "created_by"

    def get_queryset(self):
        queryset = super().get_queryset()
        if getattr(self, "swagger_fake_view", False):
            return queryset.none()
        return queryset.filter(**{self.owner_lookup: self.request.user})


class CreatedByMixin:
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
