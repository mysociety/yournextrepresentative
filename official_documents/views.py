from __future__ import unicode_literals

from django.views.generic import CreateView, DetailView
from django.template.loader import render_to_string
from django.shortcuts import get_object_or_404

from auth_helpers.views import GroupRequiredMixin
from elections.mixins import ElectionMixin
from moderation_queue.models import SuggestedPostLock

from .forms import UploadDocumentForm
from .models import DOCUMENT_UPLOADERS_GROUP_NAME, OfficialDocument

from popolo.models import Post
from candidates.models import is_post_locked


class DocumentView(DetailView):
    model = OfficialDocument

    def get_context_data(self, **kwargs):
        context = super(DocumentView, self).get_context_data(**kwargs)
        post = get_object_or_404(Post, id=self.object.post_id)
        context['post_label'] = post.label
        return context


class CreateDocumentView(ElectionMixin, GroupRequiredMixin, CreateView):
    required_group_name = DOCUMENT_UPLOADERS_GROUP_NAME

    form_class = UploadDocumentForm
    template_name = "official_documents/upload_document_form.html"

    def get_initial(self):
        post = get_object_or_404(Post, extra__slug=self.kwargs['post_id'])
        return {
            'election': self.election_data,
            'document_type': OfficialDocument.NOMINATION_PAPER,
            'post': post,
        }

    def get_context_data(self, **kwargs):
        context = super(CreateDocumentView, self).get_context_data(**kwargs)
        post = get_object_or_404(Post, extra__slug=self.kwargs['post_id'])
        context['post_label'] = post.label
        return context


class PostsForDocumentView(DetailView):
    model = OfficialDocument
    template_name = "official_documents/posts_for_document.html"

    def get_context_data(self, **kwargs):
        context = super(PostsForDocumentView, self).get_context_data(**kwargs)
        documents = OfficialDocument.objects.filter(
            source_url=self.object.source_url
        ).select_related(
            'post__extra', 'election'
        )

        """
        This might seem a bit inefficient but there's not likely to
        be many posts here and this page isn't used much. And rewriting
        the query to gather this information in a single go is going to
        make the code and the template unpleasant.
        """
        context['document_posts'] = [
            (
                document,
                is_post_locked(document.post, document.election),
                SuggestedPostLock.objects.filter(
                    postextraelection__postextra=document.post.extra,
                    postextraelection__election=document.election,
                ).exists()
            )
            for document in documents
        ]
        return context


def get_add_from_document_cta_flash_message(document, remaining_posts):
    return render_to_string(
        'official_documents/_add_from_document_cta_flash_message.html',
        {
            'document': document,
            'remaining_posts': remaining_posts,
        }
    )
