from django.template.response import TemplateResponse


class RenderTemplateResponseMiddleware:
    """Ensure TemplateResponse (and subclasses) are rendered before later middleware.

    This avoids ContentNotRenderedError when later middleware accesses response.content.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        # Render Django TemplateResponse early
        if isinstance(response, TemplateResponse):
            response = response.render()
        else:
            # Render DRF Response (or similar) if not yet rendered
            # DRF Response provides .render() and .is_rendered attributes
            has_render = hasattr(response, "render")
            has_is_rendered = hasattr(response, "is_rendered")
            has_accepted_renderer = hasattr(response, "accepted_renderer")
            if (
                has_render
                and has_is_rendered
                and not getattr(response, "is_rendered")
                and has_accepted_renderer
                and getattr(response, "accepted_renderer") is not None
            ):
                response = response.render()
        return response


