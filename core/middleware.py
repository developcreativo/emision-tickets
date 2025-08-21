from django.template.response import TemplateResponse

try:
    from rest_framework.renderers import JSONRenderer
except Exception:  # DRF may not be installed in some contexts
    JSONRenderer = None


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
            if has_render and has_is_rendered and not getattr(response, "is_rendered"):
                # Prefer rendering via DRF's negotiated renderer if available
                if has_accepted_renderer and getattr(response, "accepted_renderer") is not None:
                    response = response.render()
                # Fallback: force JSON rendering to ensure .content exists before CommonMiddleware
                elif JSONRenderer is not None:
                    try:
                        response.accepted_renderer = JSONRenderer()
                        response.accepted_media_type = "application/json"
                        response.renderer_context = {
                            "request": request,
                            "response": response,
                            "args": (),
                            "kwargs": {},
                            "view": None,
                        }
                        response = response.render()
                    except Exception:
                        # As a last resort, leave unrendered
                        pass
        return response


