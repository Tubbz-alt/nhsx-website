from django.db import models
from django.shortcuts import render
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import HttpResponse
from django.template import loader
from django.utils.text import slugify
from django.http import Http404


from wagtail.admin.edit_handlers import FieldPanel, StreamFieldPanel
from wagtail.contrib.routable_page.models import RoutablePageMixin, route
from wagtail.core.models import Page

from modules.core.models.abstract import BasePage
from modules.core.models.pages import SectionPage, ArticlePage
from modules.blog_posts.models import BlogPost

from modules.ai_lab.models.resources import (
    AiLabCaseStudy,
    AiLabExternalResource,
    AiLabTopic,
    AiLabGuidance,
    AiLabReport,
)


class AiLabFilterableResourceMixin(RoutablePageMixin):
    @route(r"^$")
    @route(r"^topic/([a-z\-0-9]+)/$")
    def filter_by_topic(self, request, topic=None, resource_type=None):
        resources = self._get_resources(topic, resource_type).live()
        template = self.get_template(request)
        topics = AiLabTopic.objects.all()

        paginator = Paginator(resources, 9)

        page = request.GET.get("page")

        try:
            resources = paginator.page(page)
        except PageNotAnInteger:
            resources = paginator.page(1)
        except EmptyPage:
            resources = paginator.page(paginator.num_pages)

        response = self._render(
            request,
            template,
            {
                "resources": resources,
                "page": self,
                "topics": topics,
                "topic": topic,
                "paginator": paginator,
            },
        )

        return response

    def _render(self, request, template, context):
        t = loader.get_template(template)
        response = HttpResponse(t.render(context, request))
        if context["resources"].has_next():
            response["next_page"] = context["resources"].next_page_number()
        return response

    def _get_resources(self, topic=None, resource_type=None):
        if topic is None:
            resources = self.get_children().specific()
        else:
            resources = self._filter_by_topic(topic)

        if resource_type is None:
            return resources
        else:
            return resources.type(resource_type)

    def _filter_by_topic(self, topic):
        ids = self._get_ids_for_topic(topic)

        return Page.objects.filter(id__in=(ids)).specific()

    def _get_ids_for_topic(self, topic):
        ids = []

        for resource_ids_for_use_case in [
            self._get_ids_for_class(klass, topic) for klass in self.subpage_types
        ]:
            for id in resource_ids_for_use_case:
                ids.append(id)

        return ids

    def _get_ids_for_class(self, klass, topic):
        return (
            eval(klass)
            .objects.child_of(self)
            .filter(topics__slug=topic)
            .values_list("id", flat=True)
        )

    @route(r"^type/([a-z\-0-9]+)/$")
    @route(r"^type/([a-z\-0-9]+)/topic/([a-z\-0-9]+)/$")
    def filter_by_type(self, request, resource_type, topic=None):
        resource_type = self._subpage_types()[resource_type]

        if resource_type:
            return self.filter_by_topic(request, topic, resource_type)
        else:
            raise Http404("Nothing found")

    def _subpage_types(self):
        types = {}
        for t in AiLabCategoryIndexPageMixin.subpage_types:
            klass = eval(t)
            key = slugify(klass._meta.verbose_name)
            types[key] = klass

        return types


class AiLabResourceIndexPage(AiLabFilterableResourceMixin, BasePage):
    """
    An index page that lists all resources listed in the child
    sections
    """

    ajax_template = "ai_lab/ai_lab_resource_index_page.js.html"

    parent_page_types = ["AiLabHomePage"]
    subpage_types = [
        "AiLabUnderstandIndexPage",
        "AiLabDevelopIndexPage",
        "AiLabAdoptIndexPage",
    ]

    sub_head = models.CharField(max_length=255, blank=True, null=True)

    content_panels = [
        FieldPanel("title"),
        FieldPanel("sub_head"),
        StreamFieldPanel("body"),
    ]

    def _get_resources(self, topic=None, resource_type=None):
        resource_ids = []
        children = self.get_children().specific()

        for child in children:
            if topic is None:
                for resource in child.get_children().specific():
                    resource_ids.append(resource.id)
            else:
                for id in child._get_ids_for_topic(topic):
                    resource_ids.append(id)

        resources = (
            Page.objects.filter(id__in=resource_ids).specific().order_by("title")
        )

        if resource_type is None:
            return resources
        else:
            return resources.type(resource_type)


class AiLabCategoryIndexPageMixin(AiLabFilterableResourceMixin, SectionPage):
    """
    A Mixin to be used by the category listing index pages
    """

    parent_page_types = ["AiLabResourceIndexPage"]
    subpage_types = [
        "AiLabCaseStudy",
        "AiLabExternalResource",
        "AiLabGuidance",
        "AiLabReport",
    ]
    max_count = 1

    summary_title = models.CharField(
        max_length=100,
        help_text="The title that will appear on the resource index page",
    )
    summary_body = models.CharField(
        max_length=255,
        help_text="The description that will appear on the resource index page",
    )

    content_panels = [
        FieldPanel("title"),
        FieldPanel("sub_head"),
        FieldPanel("summary_title"),
        FieldPanel("summary_body"),
    ]

    class Meta:
        abstract = True


class AiLabUnderstandIndexPage(AiLabCategoryIndexPageMixin):

    template = "ai_lab/ai_lab_category_index_page.html"
    ajax_template = "ai_lab/ai_lab_resource_index_page.js.html"

    class Meta:
        verbose_name = "Understanding AI Index Page"


class AiLabDevelopIndexPage(AiLabCategoryIndexPageMixin):

    template = "ai_lab/ai_lab_category_index_page.html"
    ajax_template = "ai_lab/ai_lab_resource_index_page.js.html"

    class Meta:
        verbose_name = "Developing AI Index Page"


class AiLabAdoptIndexPage(AiLabCategoryIndexPageMixin):

    template = "ai_lab/ai_lab_category_index_page.html"
    ajax_template = "ai_lab/ai_lab_resource_index_page.js.html"

    class Meta:
        verbose_name = "Adopting AI Index Page"