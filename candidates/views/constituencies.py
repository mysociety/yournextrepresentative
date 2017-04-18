from __future__ import unicode_literals

from datetime import timedelta

from slugify import slugify

from django.views.decorators.cache import cache_control
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.utils.decorators import method_decorator
from django.utils.http import urlquote
from django.utils.translation import ugettext as _
from django.views.generic import TemplateView, FormView, View
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.db.models import Prefetch

from elections.mixins import ElectionMixin
from auth_helpers.views import GroupRequiredMixin
from .helpers import (
    get_party_people_for_election_from_memberships,
    split_candidacies, get_redirect_to_post,
    group_candidates_by_party, get_person_form_fields,
    split_by_elected
)
from .version_data import get_client_ip, get_change_metadata
from ..csv_helpers import list_to_csv
from ..forms import NewPersonForm, ToggleLockForm, ConstituencyRecordWinnerForm
from ..models import (
    TRUSTED_TO_LOCK_GROUP_NAME, get_edits_allowed,
    RESULT_RECORDERS_GROUP_NAME, LoggedAction, PostExtra, OrganizationExtra,
    MembershipExtra, PartySet, SimplePopoloField, ExtraField, PostExtraElection
)
from official_documents.models import OfficialDocument
from results.models import ResultEvent
from moderation_queue.forms import SuggestedPostLockForm
from moderation_queue.models import SuggestedPostLock


from popolo.models import Membership, Post, Organization, Person


def get_max_winners(post, election):
    max_winners = election.people_elected_per_post
    post_extra_election = PostExtraElection.objects.filter(
        postextra__base=post,
        election=election,
        winner_count__isnull=False,
    ).first()
    if post_extra_election:
        max_winners = post_extra_election.winner_count

    return max_winners


class ConstituencyDetailView(ElectionMixin, TemplateView):
    template_name = 'candidates/constituency.html'

    @method_decorator(cache_control(max_age=(60 * 20)))
    def dispatch(self, *args, **kwargs):
        return super(ConstituencyDetailView, self).dispatch(
            *args, **kwargs
        )

    def get_context_data(self, **kwargs):
        from ..election_specific import shorten_post_label
        context = super(ConstituencyDetailView, self).get_context_data(**kwargs)

        context['post_id'] = post_id = kwargs['post_id']
        mp_post = get_object_or_404(
            Post.objects.select_related('extra'),
            extra__slug=post_id
        )
        context['post_obj'] = mp_post

        documents_by_type = {}
        # Make sure that every available document type has a key in
        # the dictionary, even if there are no such documents.
        doc_lookup = {t[0]: (t[1], t[2]) for t in OfficialDocument.DOCUMENT_TYPES}
        for t in doc_lookup.values():
            documents_by_type[t] = []
        documents_for_post = OfficialDocument.objects.filter(
            post_id=mp_post.id, election__slug=self.election)
        for od in documents_for_post:
            documents_by_type[doc_lookup[od.document_type]].append(od)
        context['official_documents'] = documents_by_type.items()
        context['some_official_documents'] = documents_for_post.count()

        context['post_label'] = mp_post.label
        context['post_label_shorter'] = shorten_post_label(context['post_label'])

        context['redirect_after_login'] = \
            urlquote(reverse('constituency', kwargs={
                'election': self.election,
                'post_id': post_id,
                'ignored_slug': slugify(context['post_label_shorter'])
            }))

        context['post_data'] = {
            'id': mp_post.extra.slug,
            'label': mp_post.label
        }

        context['candidates_locked'] = False

        if hasattr(mp_post, 'extra'):
            context['has_lock_suggestion'] = any(
                [spl.election_for_suggestion for spl in
                SuggestedPostLock.objects.filter(post_extra=mp_post.extra)])

            context['candidates_locked'] = mp_post.extra.candidates_locked

            context['suggest_lock_form'] = SuggestedPostLockForm(
                initial={
                    'post_extra': mp_post.extra
                },
            )

            if self.request.user.is_authenticated():
                context['user_has_suggested_lock'] = \
                    SuggestedPostLock.objects.filter(
                        user=self.request.user,
                        post_extra=mp_post.extra
                    ).exists()

        context['lock_form'] = ToggleLockForm(
            initial={
                'post_id': post_id,
                'lock': not context['candidates_locked'],
            },
        )

        context['candidate_list_edits_allowed'] = \
            get_edits_allowed(self.request.user, context['candidates_locked'])

        extra_qs = MembershipExtra.objects.select_related('election')
        current_candidacies, past_candidacies = \
            split_candidacies(
                self.election_data,
                mp_post.memberships.prefetch_related(
                    Prefetch('extra', queryset=extra_qs)
                ).select_related(
                    'person', 'person__extra', 'on_behalf_of',
                    'on_behalf_of__extra', 'organization'
                ).all()
            )

        area_2015_map = {'WMC:E14000824': u'65693', 'WMC:E14000825': u'65633', 'WMC:E14000826': u'65735', 'WMC:E14000827': u'65556', 'WMC:E14000820': u'65657', 'WMC:E14000821': u'65953', 'WMC:E14000822': u'66076', 'WMC:E14000823': u'66038', 'WMC:E14000828': u'65815', 'WMC:E14000829': u'65696', 'WMC:E14000948': u'65829', 'WMC:E14000543': u'66006', 'WMC:E14000810': u'65647', 'WMC:E14000813': u'65718', 'WMC:E14000540': u'65662', 'WMC:E14000699': u'65857', 'WMC:E14000751': u'66069', 'WMC:E14000546': u'65711', 'WMC:S14000048': u'14445', 'WMC:S14000049': u'14446', 'WMC:E14000912': u'65889', 'WMC:E14000913': u'65891', 'WMC:E14000914': u'66027', 'WMC:E14000915': u'65763', 'WMC:E14000916': u'65706', 'WMC:E14000917': u'65842', 'WMC:S14000040': u'14436', 'WMC:S14000041': u'14437', 'WMC:S14000042': u'14438', 'WMC:S14000043': u'14439', 'WMC:S14000044': u'14440', 'WMC:S14000045': u'14441', 'WMC:S14000046': u'14442', 'WMC:S14000047': u'14443', 'WMC:E14000727': u'65576', 'WMC:E14000726': u'65836', 'WMC:E14000725': u'65915', 'WMC:E14000724': u'65671', 'WMC:E14000723': u'65599', 'WMC:E14000649': u'65636', 'WMC:E14000721': u'65752', 'WMC:E14000720': u'65550', 'WMC:E14000644': u'65926', 'WMC:E14000645': u'65835', 'WMC:E14000646': u'65771', 'WMC:E14000690': u'65816', 'WMC:E14000640': u'65734', 'WMC:W07000063': u'66111', 'WMC:E14000642': u'66030', 'WMC:E14000643': u'66057', 'WMC:E14001034': u'65629', 'WMC:E14001035': u'65758', 'WMC:E14001036': u'65851', 'WMC:E14001037': u'65963', 'WMC:E14001030': u'66047', 'WMC:E14001031': u'65716', 'WMC:E14001032': u'66058', 'WMC:E14001033': u'65873', 'WMC:E14000544': u'65898', 'WMC:E14001038': u'65742', 'WMC:E14001039': u'65612', 'WMC:E14000965': u'66067', 'WMC:E14000964': u'65854', 'WMC:E14000967': u'65960', 'WMC:E14000966': u'65907', 'WMC:S14000039': u'14435', 'WMC:S14000038': u'14434', 'WMC:E14000963': u'65732', 'WMC:E14000962': u'66073', 'WMC:S14000035': u'14431', 'WMC:S14000034': u'14430', 'WMC:S14000037': u'14433', 'WMC:S14000036': u'14432', 'WMC:E14000969': u'65606', 'WMC:E14000968': u'65571', 'WMC:S14000033': u'14429', 'WMC:S14000032': u'14428', 'WMC:E14000639': u'65759', 'WMC:E14000731': u'65650', 'WMC:W07000072': u'66093', 'WMC:E14000868': u'65663', 'WMC:E14000869': u'65653', 'WMC:W07000077': u'66097', 'WMC:W07000049': u'66101', 'WMC:E14000860': u'65822', 'WMC:E14000861': u'66059', 'WMC:E14000862': u'65910', 'WMC:E14000863': u'65768', 'WMC:E14000864': u'65634', 'WMC:E14000865': u'65559', 'WMC:E14000866': u'65643', 'WMC:E14000867': u'65945', 'WMC:W07000062': u'66121', 'WMC:E14000631': u'65801', 'WMC:N06000006': u'66129', 'WMC:N06000007': u'66130', 'WMC:W07000066': u'66109', 'WMC:N06000001': u'66124', 'WMC:N06000002': u'66125', 'WMC:N06000003': u'66126', 'WMC:W07000068': u'66088', 'WMC:W07000069': u'66082', 'WMC:N06000008': u'66131', 'WMC:N06000009': u'66132', 'WMC:E14000819': u'65998', 'WMC:E14000818': u'65888', 'WMC:E14000549': u'65731', 'WMC:E14000548': u'65751', 'WMC:E14000547': u'65798', 'WMC:E14000814': u'66007', 'WMC:E14000545': u'65623', 'WMC:E14000816': u'65949', 'WMC:E14000811': u'65772', 'WMC:E14000542': u'66012', 'WMC:E14000541': u'65665', 'WMC:E14000812': u'65932', 'WMC:E14000600': u'66009', 'WMC:E14000601': u'66031', 'WMC:E14000602': u'65574', 'WMC:E14000603': u'65852', 'WMC:E14000604': u'65954', 'WMC:E14000605': u'65617', 'WMC:E14000606': u'65639', 'WMC:E14000607': u'65849', 'WMC:E14000608': u'65909', 'WMC:E14000609': u'65846', 'WMC:E14000929': u'65920', 'WMC:E14000928': u'65986', 'WMC:E14000921': u'65601', 'WMC:E14000920': u'65793', 'WMC:E14000923': u'65549', 'WMC:E14000654': u'65603', 'WMC:E14000925': u'65959', 'WMC:E14000924': u'65632', 'WMC:E14000927': u'65610', 'WMC:E14000926': u'65563', 'WMC:E14000778': u'65941', 'WMC:E14000779': u'65866', 'WMC:E14000774': u'66053', 'WMC:E14000775': u'65869', 'WMC:E14000776': u'65568', 'WMC:E14000777': u'65765', 'WMC:E14000770': u'65778', 'WMC:E14000771': u'65709', 'WMC:E14000772': u'65618', 'WMC:E14000773': u'65984', 'WMC:E14000675': u'65701', 'WMC:E14000674': u'65755', 'WMC:E14000677': u'65823', 'WMC:E14000676': u'65794', 'WMC:E14000671': u'65806', 'WMC:E14000670': u'65555', 'WMC:E14000673': u'65808', 'WMC:E14000672': u'66054', 'WMC:E14000679': u'65573', 'WMC:E14000678': u'65813', 'WMC:E14001009': u'65733', 'WMC:E14001008': u'65825', 'WMC:E14001005': u'65782', 'WMC:E14001004': u'65660', 'WMC:E14001007': u'65613', 'WMC:E14001006': u'65868', 'WMC:E14001001': u'65810', 'WMC:E14001000': u'65904', 'WMC:E14001003': u'65659', 'WMC:E14001002': u'66074', 'WMC:E14000733': u'65990', 'WMC:E14000781': u'65988', 'WMC:E14000780': u'66068', 'WMC:E14000783': u'65604', 'WMC:E14000782': u'65807', 'WMC:E14000785': u'65978', 'WMC:E14000784': u'65587', 'WMC:E14000787': u'65705', 'WMC:E14000786': u'66020', 'WMC:E14000789': u'66041', 'WMC:E14000788': u'65616', 'WMC:E14000851': u'65760', 'WMC:E14000850': u'65817', 'WMC:E14000581': u'65821', 'WMC:E14000580': u'65738', 'WMC:E14000587': u'65694', 'WMC:E14000586': u'65697', 'WMC:E14000585': u'65933', 'WMC:E14000856': u'65859', 'WMC:E14000859': u'65713', 'WMC:E14000858': u'65776', 'WMC:E14000589': u'66036', 'WMC:E14000588': u'65995', 'WMC:S14000028': u'14424', 'WMC:S14000029': u'14425', 'WMC:S14000020': u'14417', 'WMC:S14000021': u'14418', 'WMC:E14000922': u'65741', 'WMC:E14000739': u'65967', 'WMC:E14000730': u'65578', 'WMC:E14000638': u'65885', 'WMC:E14000732': u'65796', 'WMC:E14000746': u'65850', 'WMC:E14000734': u'65674', 'WMC:E14000735': u'65640', 'WMC:E14000736': u'65699', 'WMC:E14000737': u'65912', 'WMC:E14000738': u'65557', 'WMC:E14000630': u'65946', 'WMC:E14000633': u'65558', 'WMC:E14000632': u'65980', 'WMC:E14000635': u'65940', 'WMC:E14000634': u'65721', 'WMC:E14000637': u'65792', 'WMC:E14000636': u'65886', 'WMC:E14001041': u'65921', 'WMC:E14001040': u'65827', 'WMC:E14001043': u'65847', 'WMC:E14001042': u'65552', 'WMC:E14001045': u'65831', 'WMC:E14001044': u'65897', 'WMC:E14001047': u'66039', 'WMC:E14001046': u'65622', 'WMC:E14001049': u'65777', 'WMC:E14001048': u'65774', 'WMC:E14000910': u'65654', 'WMC:E14000911': u'65688', 'WMC:E14000976': u'65609', 'WMC:E14000977': u'65648', 'WMC:E14000974': u'65770', 'WMC:E14000975': u'65950', 'WMC:E14000972': u'65710', 'WMC:E14000973': u'65783', 'WMC:E14000970': u'65641', 'WMC:E14000971': u'65908', 'WMC:S14000026': u'14423', 'WMC:S14000027': u'14444', 'WMC:S14000024': u'14421', 'WMC:S14000025': u'14422', 'WMC:S14000022': u'14419', 'WMC:S14000023': u'14420', 'WMC:E14000978': u'66042', 'WMC:E14000979': u'65911', 'WMC:E14000745': u'65994', 'WMC:E14000744': u'66003', 'WMC:E14000747': u'65814', 'WMC:E14000830': u'65862', 'WMC:E14000741': u'65754', 'WMC:E14000740': u'66018', 'WMC:E14000743': u'65582', 'WMC:E14000742': u'65786', 'WMC:E14000749': u'65724', 'WMC:E14000748': u'66052', 'WMC:E14000918': u'65698', 'WMC:E14000919': u'65957', 'WMC:E14000895': u'65722', 'WMC:E14000894': u'65579', 'WMC:E14000897': u'65843', 'WMC:E14000896': u'65598', 'WMC:E14000891': u'66032', 'WMC:E14000890': u'65982', 'WMC:E14000893': u'66005', 'WMC:E14000892': u'65700', 'WMC:W07000057': u'66108', 'WMC:W07000056': u'66099', 'WMC:W07000055': u'66094', 'WMC:W07000054': u'66084', 'WMC:E14000899': u'65584', 'WMC:E14000898': u'66043', 'WMC:W07000051': u'66120', 'WMC:W07000050': u'66090', 'WMC:E14000648': u'65590', 'WMC:E14000722': u'65971', 'WMC:E14000558': u'65611', 'WMC:E14000559': u'65581', 'WMC:E14000808': u'65834', 'WMC:E14000809': u'65819', 'WMC:E14000806': u'65661', 'WMC:E14000807': u'66048', 'WMC:E14000804': u'65936', 'WMC:E14000553': u'65689', 'WMC:E14000554': u'65726', 'WMC:E14000803': u'65901', 'WMC:E14000556': u'65934', 'WMC:E14000801': u'66080', 'WMC:E14000647': u'65893', 'WMC:W07000059': u'66100', 'WMC:W07000058': u'66085', 'WMC:E14000641': u'66021', 'WMC:E14000729': u'65875', 'WMC:E14000728': u'65675', 'WMC:E14000949': u'65848', 'WMC:W07000053': u'66104', 'WMC:W07000052': u'66092', 'WMC:E14000758': u'65899', 'WMC:E14000652': u'65781', 'WMC:E14000938': u'65684', 'WMC:E14000939': u'66051', 'WMC:E14000932': u'65812', 'WMC:E14000933': u'65962', 'WMC:E14000930': u'65680', 'WMC:E14000931': u'65879', 'WMC:E14000936': u'65788', 'WMC:E14000937': u'65997', 'WMC:E14000934': u'65922', 'WMC:E14000935': u'65762', 'WMC:E14000709': u'65870', 'WMC:E14000708': u'65900', 'WMC:E14000701': u'65655', 'WMC:E14000700': u'65764', 'WMC:E14000703': u'65938', 'WMC:E14000702': u'65865', 'WMC:E14000705': u'66064', 'WMC:E14000704': u'65779', 'WMC:E14000707': u'65952', 'WMC:E14000706': u'65955', 'WMC:E14000666': u'65746', 'WMC:E14000667': u'65553', 'WMC:E14000664': u'65799', 'WMC:E14000665': u'65723', 'WMC:E14000662': u'66070', 'WMC:E14000663': u'65863', 'WMC:E14000660': u'66025', 'WMC:E14000661': u'65924', 'WMC:E14000668': u'65621', 'WMC:E14000669': u'65672', 'WMC:E14001018': u'65916', 'WMC:E14001019': u'65608', 'WMC:E14001016': u'66079', 'WMC:E14001017': u'65874', 'WMC:E14001014': u'65631', 'WMC:E14001015': u'65638', 'WMC:E14001012': u'65832', 'WMC:E14001013': u'65651', 'WMC:E14001010': u'65635', 'WMC:E14001011': u'65890', 'WMC:W07000061': u'66096', 'WMC:E14000989': u'65992', 'WMC:E14000988': u'65767', 'WMC:E14000987': u'65964', 'WMC:E14000986': u'65880', 'WMC:E14000985': u'65703', 'WMC:E14000984': u'66040', 'WMC:E14000983': u'65747', 'WMC:E14000982': u'65586', 'WMC:E14000981': u'65607', 'WMC:E14000980': u'65858', 'WMC:E14000815': u'66061', 'WMC:E14000792': u'65704', 'WMC:E14000793': u'66066', 'WMC:E14000790': u'66013', 'WMC:E14000791': u'66046', 'WMC:E14000796': u'65766', 'WMC:E14000797': u'65785', 'WMC:E14000794': u'65970', 'WMC:E14000795': u'65644', 'WMC:E14000798': u'65987', 'WMC:E14000799': u'65690', 'WMC:E14000598': u'65787', 'WMC:E14000599': u'65839', 'WMC:E14000594': u'65685', 'WMC:E14000595': u'65620', 'WMC:E14000596': u'66000', 'WMC:E14000597': u'65844', 'WMC:E14000590': u'65670', 'WMC:E14000591': u'66065', 'WMC:E14000592': u'65595', 'WMC:E14000593': u'65958', 'WMC:E14000842': u'66063', 'WMC:E14000843': u'65676', 'WMC:E14000840': u'65745', 'WMC:E14000841': u'65855', 'WMC:E14000846': u'65619', 'WMC:E14000847': u'65642', 'WMC:E14000844': u'65729', 'WMC:E14000845': u'65840', 'WMC:E14000848': u'65872', 'WMC:E14000849': u'66017', 'WMC:E14000817': u'65999', 'WMC:E14000561': u'65667', 'WMC:E14000560': u'65931', 'WMC:E14000563': u'66072', 'WMC:E14000562': u'65597', 'WMC:E14000565': u'65966', 'WMC:E14000564': u'65989', 'WMC:E14000567': u'65804', 'WMC:E14000566': u'66028', 'WMC:E14000569': u'65820', 'WMC:E14000568': u'65707', 'WMC:E14000961': u'65591', 'WMC:E14000960': u'65715', 'WMC:E14000628': u'65797', 'WMC:E14000629': u'65818', 'WMC:E14000622': u'65914', 'WMC:E14000623': u'65749', 'WMC:E14000620': u'65929', 'WMC:E14000621': u'65972', 'WMC:E14000626': u'66075', 'WMC:E14000627': u'65727', 'WMC:E14000624': u'65748', 'WMC:E14000625': u'65615', 'WMC:S14000031': u'14427', 'WMC:S14000030': u'14426', 'WMC:E14001052': u'65577', 'WMC:E14001053': u'65625', 'WMC:E14001050': u'65593', 'WMC:E14001051': u'65948', 'WMC:E14001056': u'66010', 'WMC:E14001057': u'65695', 'WMC:E14001054': u'65757', 'WMC:E14001055': u'65562', 'WMC:E14001058': u'66078', 'WMC:E14001059': u'65669', 'WMC:E14000943': u'65951', 'WMC:E14000942': u'65902', 'WMC:E14000941': u'65666', 'WMC:E14000940': u'66034', 'WMC:E14000947': u'65800', 'WMC:E14000946': u'65614', 'WMC:E14000945': u'65943', 'WMC:E14000944': u'65719', 'WMC:S14000013': u'14410', 'WMC:S14000012': u'14409', 'WMC:S14000011': u'14408', 'WMC:S14000010': u'14407', 'WMC:S14000017': u'14414', 'WMC:S14000016': u'14413', 'WMC:S14000015': u'14412', 'WMC:S14000014': u'14411', 'WMC:E14000756': u'65624', 'WMC:E14000757': u'65592', 'WMC:E14000754': u'65947', 'WMC:E14000755': u'65691', 'WMC:E14000752': u'65883', 'WMC:E14000753': u'65717', 'WMC:E14000750': u'65824', 'WMC:E14000698': u'66033', 'WMC:E14000697': u'66062', 'WMC:E14000696': u'66023', 'WMC:E14000695': u'65743', 'WMC:E14000694': u'65803', 'WMC:E14000693': u'66044', 'WMC:E14000692': u'65567', 'WMC:E14000691': u'66050', 'WMC:E14000759': u'65630', 'WMC:E14000886': u'65637', 'WMC:E14000887': u'66045', 'WMC:E14000884': u'66014', 'WMC:E14000885': u'65673', 'WMC:E14000882': u'65917', 'WMC:E14000883': u'65566', 'WMC:E14000880': u'65737', 'WMC:E14000881': u'65860', 'WMC:W07000041': u'66115', 'WMC:W07000042': u'66112', 'WMC:W07000043': u'66103', 'WMC:W07000044': u'66113', 'WMC:W07000045': u'66117', 'WMC:E14000888': u'65795', 'WMC:E14000889': u'65973', 'WMC:E14000550': u'65687', 'WMC:E14000551': u'65725', 'WMC:E14000552': u'65561', 'WMC:E14000805': u'65645', 'WMC:E14000901': u'65884', 'WMC:E14000802': u'65896', 'WMC:E14000900': u'66077', 'WMC:E14000555': u'65853', 'WMC:E14000800': u'65887', 'WMC:E14000557': u'65845', 'WMC:E14000688': u'65991', 'WMC:E14000689': u'65677', 'WMC:E14000839': u'65702', 'WMC:E14000838': u'65658', 'WMC:S14000051': u'14448', 'WMC:E14000833': u'65664', 'WMC:E14000832': u'65594', 'WMC:E14000831': u'66055', 'WMC:E14000908': u'65736', 'WMC:E14000837': u'65602', 'WMC:E14000836': u'65918', 'WMC:E14000835': u'65828', 'WMC:E14000834': u'65861', 'WMC:E14000583': u'66071', 'WMC:E14000582': u'65969', 'WMC:E14000853': u'65720', 'WMC:E14000852': u'65605', 'WMC:E14000855': u'65565', 'WMC:W07000048': u'66091', 'WMC:E14000682': u'65780', 'WMC:E14000854': u'66024', 'WMC:E14000683': u'65979', 'WMC:E14000857': u'65894', 'WMC:E14000584': u'65993', 'WMC:E14000538': u'65739', 'WMC:E14000539': u'66008', 'WMC:E14000536': u'65811', 'WMC:E14000537': u'66056', 'WMC:E14000534': u'65784', 'WMC:E14000535': u'65895', 'WMC:E14000532': u'65892', 'WMC:E14000533': u'65809', 'WMC:E14000530': u'65730', 'WMC:E14000531': u'65773', 'WMC:E14000907': u'65589', 'WMC:E14000906': u'65681', 'WMC:E14000905': u'65656', 'WMC:E14000904': u'66029', 'WMC:E14000903': u'65930', 'WMC:E14000902': u'66019', 'WMC:S14000059': u'14456', 'WMC:S14000058': u'14455', 'WMC:S14000057': u'14454', 'WMC:S14000056': u'14453', 'WMC:S14000055': u'14452', 'WMC:S14000054': u'14451', 'WMC:S14000053': u'14450', 'WMC:S14000052': u'14449', 'WMC:E14000909': u'65833', 'WMC:S14000050': u'14447', 'WMC:E14000718': u'65837', 'WMC:E14000719': u'65838', 'WMC:E14000712': u'65996', 'WMC:E14000713': u'65928', 'WMC:E14000710': u'65551', 'WMC:E14000711': u'65864', 'WMC:E14000716': u'65600', 'WMC:E14000717': u'65627', 'WMC:E14000714': u'65683', 'WMC:E14000715': u'65944', 'WMC:E14000653': u'65572', 'WMC:N06000004': u'66127', 'WMC:E14000651': u'65877', 'WMC:E14000650': u'65575', 'WMC:E14000657': u'65985', 'WMC:E14000656': u'65923', 'WMC:E14000655': u'65867', 'WMC:N06000005': u'66128', 'WMC:E14000659': u'66011', 'WMC:E14000658': u'65802', 'WMC:W07000060': u'66116', 'WMC:E14001029': u'65983', 'WMC:E14001028': u'65588', 'WMC:E14001023': u'65961', 'WMC:E14001022': u'66004', 'WMC:E14001021': u'65626', 'WMC:E14001020': u'66049', 'WMC:E14001027': u'65740', 'WMC:E14001026': u'65560', 'WMC:E14001025': u'65830', 'WMC:W07000067': u'66089', 'WMC:W07000064': u'66110', 'WMC:W07000065': u'66102', 'WMC:E14000998': u'65554', 'WMC:E14000999': u'65692', 'WMC:E14000990': u'65976', 'WMC:E14000991': u'65789', 'WMC:E14000992': u'65977', 'WMC:E14000993': u'65686', 'WMC:E14000994': u'65905', 'WMC:E14000995': u'65919', 'WMC:E14000996': u'65761', 'WMC:E14000997': u'65744', 'WMC:E14000879': u'65974', 'WMC:E14000878': u'65649', 'WMC:E14000877': u'66081', 'WMC:E14000876': u'66002', 'WMC:E14000875': u'65668', 'WMC:E14000874': u'65564', 'WMC:E14000873': u'66060', 'WMC:E14000872': u'65682', 'WMC:E14000871': u'66022', 'WMC:E14000870': u'65903', 'WMC:W07000071': u'66086', 'WMC:W07000070': u'66105', 'WMC:W07000073': u'66095', 'WMC:N06000018': u'66141', 'WMC:W07000075': u'66087', 'WMC:W07000074': u'66107', 'WMC:W07000046': u'66083', 'WMC:W07000076': u'66106', 'WMC:N06000013': u'66136', 'WMC:N06000012': u'66135', 'WMC:N06000011': u'66134', 'WMC:N06000010': u'66133', 'WMC:N06000017': u'66140', 'WMC:N06000016': u'66139', 'WMC:N06000015': u'66138', 'WMC:N06000014': u'66137', 'WMC:W07000047': u'66118', 'WMC:E14001024': u'65769', 'WMC:W07000080': u'66119', 'WMC:E14000572': u'65750', 'WMC:E14000573': u'65679', 'WMC:E14000570': u'65981', 'WMC:E14000571': u'65583', 'WMC:E14000576': u'65841', 'WMC:E14000577': u'65628', 'WMC:E14000574': u'65805', 'WMC:E14000575': u'65753', 'WMC:E14000578': u'65646', 'WMC:E14000579': u'65712', 'WMC:W07000079': u'66114', 'WMC:E14000617': u'65927', 'WMC:E14000616': u'65826', 'WMC:E14000615': u'65913', 'WMC:E14000614': u'65906', 'WMC:E14000613': u'66035', 'WMC:E14000612': u'65975', 'WMC:E14000611': u'66015', 'WMC:E14000610': u'65708', 'WMC:E14000619': u'65878', 'WMC:E14000618': u'65790', 'WMC:W07000078': u'66098', 'WMC:E14001062': u'66037', 'WMC:E14001061': u'65965', 'WMC:E14001060': u'65935', 'WMC:E14000958': u'65728', 'WMC:E14000959': u'65942', 'WMC:E14000954': u'65956', 'WMC:E14000955': u'66016', 'WMC:E14000956': u'65580', 'WMC:E14000957': u'65876', 'WMC:E14000950': u'65775', 'WMC:E14000951': u'65596', 'WMC:E14000952': u'65652', 'WMC:E14000953': u'65678', 'WMC:S14000004': u'14401', 'WMC:S14000005': u'14402', 'WMC:S14000006': u'14403', 'WMC:S14000007': u'14404', 'WMC:S14000001': u'14398', 'WMC:S14000002': u'14399', 'WMC:S14000003': u'14400', 'WMC:S14000008': u'14405', 'WMC:S14000009': u'14406', 'WMC:E14000763': u'65937', 'WMC:E14000762': u'65791', 'WMC:E14000761': u'65925', 'WMC:E14000760': u'65585', 'WMC:E14000767': u'65968', 'WMC:E14000766': u'65871', 'WMC:E14000765': u'66026', 'WMC:E14000764': u'65882', 'WMC:E14000680': u'65569', 'WMC:E14000681': u'65856', 'WMC:E14000769': u'66001', 'WMC:E14000768': u'65939', 'WMC:E14000684': u'65714', 'WMC:E14000685': u'65881', 'WMC:E14000686': u'65756', 'WMC:E14000687': u'65570', 'WMC:S14000019': u'14416', 'WMC:S14000018': u'14415'}
        #HACK
        slug = area_2015_map.get(mp_post.extra.slug)
        current_candidacies_2015 = set()
        past_candidacies_2015 = set()
        if slug:
            other_post = Post.objects.get(extra__slug=slug)
            current_candidacies_2015, past_candidacies_2015 = \
                split_candidacies(
                    self.election_data,
                    other_post.memberships.prefetch_related(
                        Prefetch('extra', queryset=extra_qs)
                    ).select_related(
                        'person', 'person__extra', 'on_behalf_of',
                        'on_behalf_of__extra', 'organization'
                    ).all()
                )

        # HACK

        past_candidacies = past_candidacies.union(past_candidacies_2015)

        current_candidates = set(c.person for c in current_candidacies)
        past_candidates = set(c.person for c in past_candidacies)

        current_candidates = current_candidates.union(set(c.person for c in current_candidacies_2015))
        past_candidates = past_candidates.union(set(c.person for c in past_candidacies_2015))

        other_candidates = past_candidates - current_candidates

        elected, unelected = split_by_elected(
            self.election_data,
            current_candidacies,
        )

        # Now split those candidates into those that we know aren't
        # standing again, and those that we just don't know about.
        not_standing_candidates = set(
            p for p in other_candidates
            if self.election_data in p.extra.not_standing.all()
        )
        might_stand_candidates = set(
            p for p in other_candidates
            if self.election_data not in p.extra.not_standing.all()
        )

        not_standing_candidacies = [c for c in past_candidacies
                                    if c.person in not_standing_candidates]
        might_stand_candidacies = [c for c in past_candidacies
                                   if c.person in might_stand_candidates]

        context['candidacies_not_standing_again'] = \
            group_candidates_by_party(
                self.election_data,
                not_standing_candidacies,
            )

        context['candidacies_might_stand_again'] = \
            group_candidates_by_party(
                self.election_data,
                might_stand_candidacies,
            )

        context['elected'] = group_candidates_by_party(
            self.election_data,
            elected,
            show_all=True,
        )

        context['unelected'] = group_candidates_by_party(
            self.election_data,
            unelected,
        )

        context['has_elected'] = \
            len(context['elected']['parties_and_people']) > 0

        context['show_retract_result'] = False
        number_of_winners = 0
        for c in current_candidacies:
            if c.extra.elected:
                number_of_winners += 1
            if c.extra.elected is not None:
                context['show_retract_result'] = True

        max_winners = get_max_winners(mp_post, self.election_data)
        context['show_confirm_result'] = (max_winners < 0) \
            or number_of_winners < max_winners

        context['add_candidate_form'] = NewPersonForm(
            election=self.election,
            initial={
                ('constituency_' + self.election): post_id,
                ('standing_' + self.election): 'standing',
            },
            hidden_post_widget=True,
        )

        context = get_person_form_fields(
            context,
            context['add_candidate_form']
        )
        return context


class ConstituencyDetailCSVView(ElectionMixin, View):

    http_method_names = ['get']

    def get(self, request, *args, **kwargs):
        post = Post.objects \
            .select_related('extra') \
            .get(extra__slug=kwargs['post_id'])
        all_people = []
        for me in MembershipExtra.objects \
                .filter(
                    election=self.election_data,
                    base__post=post
                ) \
                .select_related('base__person') \
                .prefetch_related('base__person__extra'):
            for d in me.base.person.extra.as_list_of_dicts(self.election_data):
                all_people.append(d)

        filename = "{election}-{constituency_slug}.csv".format(
            election=self.election,
            constituency_slug=slugify(post.extra.short_label),
        )
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="%s"' % filename
        response.write(list_to_csv(all_people))
        return response


class ConstituencyListView(ElectionMixin, TemplateView):
    template_name = 'candidates/constituencies.html'

    def get_context_data(self, **kwargs):
        context = super(ConstituencyListView, self).get_context_data(**kwargs)
        context['all_constituencies'] = \
            PostExtra.objects.filter(
                elections__slug=self.election
            ).order_by('base__label').select_related('base')

        return context


class ConstituencyLockView(ElectionMixin, GroupRequiredMixin, View):
    required_group_name = TRUSTED_TO_LOCK_GROUP_NAME

    http_method_names = ['post']

    def post(self, request, *args, **kwargs):
        form = ToggleLockForm(data=self.request.POST)
        if form.is_valid():
            post_id = form.cleaned_data['post_id']
            with transaction.atomic():
                post = get_object_or_404(Post, extra__slug=post_id)
                lock = form.cleaned_data['lock']
                post.extra.candidates_locked = lock
                post.extra.save()
                post_name = post.extra.short_label
                if lock:
                    suffix = '-lock'
                    pp = 'Locked'
                else:
                    suffix = '-unlock'
                    pp = 'Unlocked'
                message = pp + ' constituency {0} ({1})'.format(
                    post_name, post.id
                )

                LoggedAction.objects.create(
                    user=self.request.user,
                    action_type=('constituency' + suffix),
                    ip_address=get_client_ip(self.request),
                    source=message,
                )
            return HttpResponseRedirect(
                reverse('constituency', kwargs={
                    'election': self.election,
                    'post_id': post_id,
                    'ignored_slug': slugify(post_name),
                })
            )
        else:
            message = _('Invalid data POSTed to ConstituencyLockView')
            raise ValidationError(message)


class ConstituenciesUnlockedListView(ElectionMixin, TemplateView):
    template_name = 'candidates/constituencies-unlocked.html'

    def get_context_data(self, **kwargs):
        context = super(ConstituenciesUnlockedListView, self).get_context_data(**kwargs)
        total_constituencies = 0
        total_locked = 0
        keys = ('locked', 'unlocked')
        for k in keys:
            context[k] = []
        posts = Post.objects.filter(
            extra__elections=self.election_data
        ).select_related('extra').all()
        for post in posts:
            total_constituencies += 1
            if post.extra.candidates_locked:
                context_field = 'locked'
                total_locked += 1
            else:
                context_field = 'unlocked'
            context[context_field].append(
                {
                    'id': post.extra.slug,
                    'name': post.extra.short_label,
                }
            )
        for k in keys:
            context[k].sort(key=lambda c: c['name'])
        context['total_constituencies'] = total_constituencies
        context['total_left'] = total_constituencies - total_locked
        if total_constituencies > 0:
            context['percent_done'] = (100 * total_locked) // total_constituencies
        else:
            context['percent_done'] = 0
        return context

class ConstituencyRecordWinnerView(ElectionMixin, GroupRequiredMixin, FormView):

    form_class = ConstituencyRecordWinnerForm
    # TODO: is this template ever used?
    template_name = 'candidates/record-winner.html'
    required_group_name = RESULT_RECORDERS_GROUP_NAME

    def dispatch(self, request, *args, **kwargs):
        person_id = self.request.POST.get(
            'person_id',
            self.request.GET.get('person', '')
        )
        self.person = get_object_or_404(Person, id=person_id)
        self.post_data = get_object_or_404(Post, extra__slug=self.kwargs['post_id'])

        return super(ConstituencyRecordWinnerView, self). \
            dispatch(request, *args, **kwargs)

    def get_initial(self):
        initial = super(ConstituencyRecordWinnerView, self). \
            get_initial()
        initial['person_id'] = self.person.id
        return initial

    def get_context_data(self, **kwargs):
        context = super(ConstituencyRecordWinnerView, self). \
            get_context_data(**kwargs)
        context['post_id'] = self.kwargs['post_id']
        context['constituency_name'] = self.post_data.label
        context['person'] = self.person
        return context

    def form_valid(self, form):
        change_metadata = get_change_metadata(
            self.request,
            form.cleaned_data['source']
        )

        with transaction.atomic():
            number_of_existing_winners = self.post_data.memberships.filter(
                extra__elected=True,
                extra__election=self.election_data
            ).count()
            max_winners = get_max_winners(self.post_data, self.election_data)
            if max_winners >= 0 and number_of_existing_winners >= max_winners:
                msg = "There were already {n} winners of {post_label}" \
                    "and the maximum in election {election_name} is {max}"
                raise Exception(msg.format(
                    n=number_of_existing_winners,
                    post_label=self.post_data.label,
                    election_name=self.election_data.name,
                    max=self.election_data.people_elected_per_post
                ))
            # So now we know we can set this person as the winner:
            candidate_role = self.election_data.candidate_membership_role
            membership_new_winner = Membership.objects.get(
                role=candidate_role,
                post=self.post_data,
                person=self.person,
                extra__election=self.election_data,
            )
            membership_new_winner.extra.elected = True
            membership_new_winner.extra.save()

            ResultEvent.objects.create(
                election=self.election_data,
                winner=self.person,
                winner_person_name=self.person.name,
                post_id=self.post_data.extra.slug,
                post_name=self.post_data.label,
                winner_party_id=membership_new_winner.on_behalf_of.extra.slug,
                source=form.cleaned_data['source'],
                user=self.request.user,
            )

            self.person.extra.record_version(change_metadata)
            self.person.save()

            LoggedAction.objects.create(
                user=self.request.user,
                action_type='set-candidate-elected',
                ip_address=get_client_ip(self.request),
                popit_person_new_version=change_metadata['version_id'],
                person=self.person,
                source=change_metadata['information_source'],
            )

            # Now, if the current number of winners is equal to the
            # maximum number of winners, we can set everyone else as
            # "not elected".
            if max_winners >= 0:
                max_reached = (max_winners == (number_of_existing_winners + 1))
                if max_reached:
                    losing_candidacies = self.post_data.memberships.filter(
                        extra__election=self.election_data,
                    ).exclude(extra__elected=True)
                    for candidacy in losing_candidacies:
                        if candidacy.extra.elected != False:
                            candidacy.extra.elected = False
                            candidacy.extra.save()
                            candidate = candidacy.person
                            change_metadata = get_change_metadata(
                                self.request,
                                _('Setting as "not elected" by implication')
                            )
                            candidate.extra.record_version(change_metadata)
                            candidate.save()

        return get_redirect_to_post(
            self.election,
            self.post_data,
        )


class ConstituencyRetractWinnerView(ElectionMixin, GroupRequiredMixin, View):

    required_group_name = RESULT_RECORDERS_GROUP_NAME
    http_method_names = ['post']

    def post(self, request, *args, **kwargs):
        post_id = self.kwargs['post_id']
        post = get_object_or_404(Post, extra__slug=post_id)
        constituency_name = post.extra.short_label

        with transaction.atomic():
            all_candidacies = post.memberships.filter(
                role=self.election_data.candidate_membership_role,
                extra__election=self.election_data,
            )
            for candidacy in all_candidacies.all():
                if candidacy.extra.elected is not None:
                    candidacy.extra.elected = None
                    candidacy.extra.save()
                    candidate = candidacy.person
                    change_metadata = get_change_metadata(
                        self.request,
                        _('Result recorded in error, retracting')
                    )
                    candidate.extra.record_version(change_metadata)
                    candidate.save()

        return HttpResponseRedirect(
            reverse(
                'constituency',
                kwargs={
                    'post_id': post_id,
                    'election': self.election,
                    'ignored_slug': slugify(constituency_name),
                }
            )
        )


class ConstituenciesDeclaredListView(ElectionMixin, TemplateView):
    template_name = 'candidates/constituencies-declared.html'

    def get_context_data(self, **kwargs):
        context = super(ConstituenciesDeclaredListView, self).get_context_data(**kwargs)
        total_constituencies = 0
        total_declared = 0
        constituency_declared = []
        constituency_seen = {}
        constituencies = []
        total_constituencies = Post.objects.filter(
            extra__elections=self.election_data
        ).count()
        for membership in Membership.objects.select_related('post', 'post__area', 'post__extra').filter(
            post__isnull=False,
            extra__election_id=self.election_data.id,
            role=self.election_data.candidate_membership_role,
            extra__elected=True
        ):
            constituency_declared.append(membership.post.id)
            total_declared += 1
            constituencies.append((membership.post, True))
        for membership in Membership.objects.select_related('post', 'post__area', 'post__extra').filter(
            post__isnull=False,
            extra__election=self.election_data,
            role=self.election_data.candidate_membership_role
        ).exclude(post_id__in=constituency_declared):
            if constituency_seen.get(membership.post.id, False):
                continue
            constituency_seen[membership.post.id] = True
            constituencies.append((membership.post, False))
        constituencies.sort(key=lambda c: c[0].area.name)
        context['constituencies'] = constituencies
        context['total_constituencies'] = total_constituencies
        context['total_left'] = total_constituencies - total_declared
        if total_constituencies > 0:
            context['percent_done'] = (100 * total_declared) // total_constituencies
        else:
            context['percent_done'] = 0
        return context


class OrderedPartyListView(ElectionMixin, TemplateView):
    template_name = 'candidates/ordered-party-list.html'

    @method_decorator(cache_control(max_age=(60 * 20)))
    def dispatch(self, *args, **kwargs):
        return super(OrderedPartyListView, self).dispatch(
            *args, **kwargs
        )

    def get_context_data(self, **kwargs):
        from ..election_specific import shorten_post_label
        context = super(OrderedPartyListView, self).get_context_data(**kwargs)

        context['post_id'] = post_id = kwargs['post_id']
        post_qs = Post.objects.select_related('extra')
        mp_post = get_object_or_404(post_qs, extra__slug=post_id)

        party_id = kwargs['organization_id']
        party = get_object_or_404(Organization, extra__slug=party_id)

        context['party'] = party

        context['post_label'] = mp_post.label
        context['post_label_shorter'] = shorten_post_label(context['post_label'])

        context['redirect_after_login'] = \
            urlquote(reverse('party-for-post', kwargs={
                'election': self.election,
                'post_id': post_id,
                'organization_id': party_id
            }))

        context['post_data'] = {
            'id': mp_post.extra.slug,
            'label': mp_post.label
        }

        context['candidates_locked'] = mp_post.extra.candidates_locked
        context['lock_form'] = ToggleLockForm(
            initial={
                'post_id': post_id,
                'lock': not context['candidates_locked'],
            },
        )
        context['candidate_list_edits_allowed'] = \
            get_edits_allowed(self.request.user, context['candidates_locked'])

        context['positions_and_people'] = \
            get_party_people_for_election_from_memberships(
                self.election, party.id, mp_post.memberships
            )

        party_set = PartySet.objects.get(postextra__slug=post_id)

        context['add_candidate_form'] = NewPersonForm(
            election=self.election,
            initial={
                ('constituency_' + self.election): post_id,
                ('standing_' + self.election): 'standing',
                ('party_' + party_set.slug + '_' + self.election): party_id,
            },
            hidden_post_widget=True,
        )

        return context
