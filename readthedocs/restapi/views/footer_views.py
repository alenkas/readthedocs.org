from django.shortcuts import get_object_or_404
from django.template import Context, loader as template_loader
from django.conf import settings
from django.core.context_processors import csrf

from rest_framework import decorators, permissions
from rest_framework.renderers import JSONPRenderer, JSONRenderer, BrowsableAPIRenderer
from rest_framework.response import Response

from bookmarks.models import Bookmark
from builds.models import Version
from projects.models import Project


@decorators.api_view(['GET'])
@decorators.permission_classes((permissions.AllowAny,))
@decorators.renderer_classes((JSONRenderer, JSONPRenderer, BrowsableAPIRenderer))
def footer_html(request):
    project_slug = request.GET.get('project', None)
    version_slug = request.GET.get('version', None)
    page_slug = request.GET.get('page', None)
    theme = request.GET.get('theme', False)
    docroot = request.GET.get('docroot', '')
    subproject = request.GET.get('subproject', False)
    source_suffix = request.GET.get('source_suffix', '.rst')

    new_theme = (theme == "sphinx_rtd_theme")
    using_theme = (theme == "default")
    project = get_object_or_404(Project, slug=project_slug)
    version = get_object_or_404(Version.objects.public(request.user, project=project, only_active=False), slug=version_slug)
    main_project = project.main_language_project or project

    if page_slug and page_slug != "index":
        if main_project.documentation_type == "sphinx_htmldir" or main_project.documentation_type == "mkdocs":
            path = page_slug + "/"
        elif main_project.documentation_type == "sphinx_singlehtml":
            path = "index.html#document-" + page_slug
        else:
            path = page_slug + ".html"
    else:
        path = ""

    host = request.get_host()
    if settings.PRODUCTION_DOMAIN in host and request.user.is_authenticated():
        show_bookmarks = True
        try:
            bookmark = Bookmark.objects.get(
                user=request.user,
                project=project,
                version=version,
                page=page_slug,
            )
        except (Bookmark.DoesNotExist, Bookmark.MultipleObjectsReturned, Exception):
            bookmark = None
    else:
        show_bookmarks = False
        bookmark = None

    if version.type == 'tag' and version.project.has_pdf(version.slug):
        print_url = 'https://keminglabs.com/print-the-docs/quote?project={project}&version={version}'.format(
            project=project.slug,
            version=version.slug,
        )
    else:
        print_url = None

    show_promo = getattr(settings, 'USE_PROMOS', True)
    # User is a gold user, no promos for them!
    if request.user.is_authenticated():
        if request.user.gold.count() or request.user.goldonce.count():
            show_promo = False
    # Explicit promo disabling
    if project.slug in getattr(settings, 'DISABLE_PROMO_PROJECTS', []):
        show_promo = False
    # A GoldUser has mapped this project
    if project.gold_owners.count():
        show_promo = False

    context = Context({
        'show_bookmarks': show_bookmarks,
        'bookmark': bookmark,
        'project': project,
        'path': path,
        'downloads': version.get_downloads(pretty=True),
        'current_version': version.verbose_name,
        'versions': project.ordered_active_versions(),
        'main_project': main_project,
        'translations': main_project.translations.all(),
        'current_language': project.language,
        'using_theme': using_theme,
        'new_theme': new_theme,
        'settings': settings,
        'subproject': subproject,
        'print_url': print_url,
        'github_edit_url': version.get_github_url(docroot, page_slug, source_suffix, 'edit'),
        'github_view_url': version.get_github_url(docroot, page_slug, source_suffix, 'view'),
        'bitbucket_url': version.get_bitbucket_url(docroot, page_slug, source_suffix),
    })

    context.update(csrf(request))
    html = template_loader.get_template('restapi/footer.html').render(context)
    return Response({
        'html': html,
        'version_active': version.active,
        'version_supported': version.supported,
        'promo': show_promo,
    })
