from django.template import RequestContext
from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect
from django.contrib.auth.models import User

from models import UserProfile

from sourcetrans.macro_module import macros, jeeves
import JeevesLib

# "Glue method". Right now you just write a method like `index` below.
# It returns a (faceted) tuple either of the form (template_name, template_ctxt)
# or ("redirect", redirect_url).
#
# SUPER HACKY, obviously. Ideally we would have a full object similar to the django
# HttpResponse that can be faceted. Such an object would need to support Jeeves,
# of course. And the concretized rendering should be moved to a library function
# (like render_to_response).
def request_wrapper(view_fn):
    def real_view_fn(request):
        try:
            profile = UserProfile.objects.get(username=request.user.username)

            ans = view_fn(request, profile)
            template_name = ans[0]
            context_dict = ans[1]

            if template_name == "redirect":
                path = context_dict
                return HttpResponseRedirect(JeevesLib.concretize(profile, path))

            concretizeState = JeevesLib.jeevesState.policyenv.getNewSolverState(profile)
            def concretize(val):
                return concretizeState.concretizeExp(val, JeevesLib.jeevesState.pathenv.getEnv())
            add_to_context(context_dict, request, template_name, profile, concretize)

            return render_to_response(template_name, RequestContext(request, context_dict))

        except Exception:
            import traceback
            traceback.print_exc()
            raise

    real_view_fn.__name__ = view_fn.__name__
    return real_view_fn

# An example of a really simple view.
# The argument `user_profile` is a UserProfile object (defined in models.py).
# Use this instead of `request.user` (which is the ordinary django User model).
# You can access request.POST and request.GET as normal.
@login_required
@request_wrapper
@jeeves
def index(request, user_profile):
    return (   "index.html"
           , { 'name' : user_profile.email } )