# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import datetime
import pytest

from h.activity import bucketing
from tests.common import factories


UTCNOW = datetime.datetime(year=1970, month=2, day=21, hour=19, minute=30)
FIVE_MINS_AGO = UTCNOW - datetime.timedelta(minutes=5)
YESTERDAY = UTCNOW - datetime.timedelta(days=1)
THIRD_MARCH_1968 = datetime.datetime(year=1968, month=3, day=3)
FIFTH_NOVEMBER_1969 = datetime.datetime(year=1969, month=11, day=5)


class TimeframeMatcher(object):

    def __init__(self, label, document_buckets):
        self.label = label
        self.document_buckets = document_buckets

    def __eq__(self, timeframe):
        return (self.label == timeframe.label and
                self.document_buckets == timeframe.document_buckets)

    def __repr__(self):
        return '{class_} "{label}" with {n} document buckets'.format(
            class_=self.__class__, label=self.label,
            n=len(self.document_buckets))


@pytest.mark.usefixtures('factories')
class TestDocumentBucket(object):
    def test_init_sets_the_document_title(self, db_session, document):
        title_meta = factories.DocumentMeta(type="title",
                                            value=["The Document Title"],
                                            document=document)
        db_session.add(title_meta)
        db_session.flush()

        bucket = bucketing.DocumentBucket(document)
        assert bucket.title == 'The Document Title'

    def test_init_extracts_the_first_http_uri(self, db_session, document):
        docuri_pdf = factories.DocumentURI(uri='urn:x-pdf:fingerprint',
                                           updated=datetime.datetime(2016, 5, 2),
                                           document=document)
        docuri_http = factories.DocumentURI(uri='http://example.com',
                                            updated=datetime.datetime(2016, 5, 1),
                                            document=document)
        db_session.add_all([docuri_pdf, docuri_http])
        db_session.flush()

        bucket = bucketing.DocumentBucket(document)
        assert bucket.uri == 'http://example.com'

    def test_init_extracts_the_first_https_uri(self, db_session, document):
        docuri_pdf = factories.DocumentURI(uri='urn:x-pdf:fingerprint',
                                           updated=datetime.datetime(2016, 5, 2),
                                           document=document)
        docuri_https = factories.DocumentURI(uri='https://example.com',
                                             updated=datetime.datetime(2016, 5, 1),
                                             document=document)
        db_session.add_all([docuri_pdf, docuri_https])
        db_session.flush()

        bucket = bucketing.DocumentBucket(document)
        assert bucket.uri == 'https://example.com'

    def test_init_sets_None_uri_when_no_http_or_https_can_be_found(self, db_session, document):
        docuri_pdf = factories.DocumentURI(uri='urn:x-pdf:fingerprint',
                                           document=document)
        db_session.add(docuri_pdf)
        db_session.flush()

        bucket = bucketing.DocumentBucket(document)
        assert bucket.uri is None

    def test_init_sets_the_domain_from_the_extracted_uri(self, db_session, document):
        docuri_https = factories.DocumentURI(uri='https://www.example.com/foobar.html',
                                             document=document)
        db_session.add(docuri_https)
        db_session.flush()

        bucket = bucketing.DocumentBucket(document)
        assert bucket.domain == 'www.example.com'

    def test_init_sets_None_domain_when_no_uri_is_set(self, db_session, document):
        docuri_pdf = factories.DocumentURI(uri='urn:x-pdf:fingerprint',
                                           document=document)
        db_session.add(docuri_pdf)
        db_session.flush()

        bucket = bucketing.DocumentBucket(document)
        assert bucket.domain is None

    def test_annotations_count_returns_count_of_annotations(self, db_session, document):
        bucket = bucketing.DocumentBucket(document)

        for _ in xrange(7):
            annotation = factories.Annotation()
            bucket.append(annotation)

        assert bucket.annotations_count == 7

    def test_append_appends_the_annotation(self, document):
        bucket = bucketing.DocumentBucket(document)

        annotations = []
        for _ in xrange(7):
            annotation = factories.Annotation()
            annotations.append(annotation)
            bucket.append(annotation)

        assert bucket.annotations == annotations

    def test_append_adds_unique_annotation_tag_to_bucket(self, document):
        ann_1 = factories.Annotation(tags=['foo', 'bar'])
        ann_2 = factories.Annotation(tags=['foo', 'baz'])

        bucket = bucketing.DocumentBucket(document)
        bucket.append(ann_1)
        bucket.append(ann_2)
        assert bucket.tags == set(['foo', 'bar', 'baz'])

    def test_append_adds_unique_annotation_user_to_bucket(self, document):
        ann_1 = factories.Annotation(userid='luke')
        ann_2 = factories.Annotation(userid='alice')
        ann_3 = factories.Annotation(userid='luke')

        bucket = bucketing.DocumentBucket(document)
        bucket.append(ann_1)
        bucket.append(ann_2)
        bucket.append(ann_3)
        assert bucket.users == set(['luke', 'alice'])

    def test_eq(self, document):
        bucket_1 = bucketing.DocumentBucket(document)
        bucket_2 = bucketing.DocumentBucket(document)

        for _ in xrange(5):
            annotation = factories.Annotation()
            bucket_1.append(annotation)
            bucket_2.append(annotation)

        assert bucket_1 == bucket_2

    def test_eq_annotations_mismatch(self, document):
        bucket_1 = bucketing.DocumentBucket(document)
        bucket_2 = bucketing.DocumentBucket(document)

        bucket_1.annotations = [1, 2, 3]
        bucket_2.annotations = [2, 3, 4]

        assert not bucket_1 == bucket_2

    def test_eq_tags_mismatch(self, document):
        bucket_1 = bucketing.DocumentBucket(document)
        bucket_2 = bucketing.DocumentBucket(document)

        bucket_1.tags.update(['foo', 'bar'])
        bucket_2.tags.update(['foo', 'baz'])

        assert not bucket_1 == bucket_2

    def test_eq_users_mismatch(self, document):
        bucket_1 = bucketing.DocumentBucket(document)
        bucket_2 = bucketing.DocumentBucket(document)

        bucket_1.users.update(['alice', 'luke'])
        bucket_2.users.update(['luke', 'paula'])

        assert not bucket_1 == bucket_2

    def test_eq_uri_mismatch(self, document):
        bucket_1 = bucketing.DocumentBucket(document)
        bucket_2 = bucketing.DocumentBucket(document)

        bucket_1.uri = 'http://example.com'
        bucket_2.uri = 'http://example.org'

        assert not bucket_1 == bucket_2

    def test_eq_domain_mismatch(self, document):
        bucket_1 = bucketing.DocumentBucket(document)
        bucket_2 = bucketing.DocumentBucket(document)

        bucket_1.domain = 'example.com'
        bucket_2.domain = 'example.org'

        assert not bucket_1 == bucket_2

    def test_eq_title_mismatch(self, document):
        bucket_1 = bucketing.DocumentBucket(document)
        bucket_2 = bucketing.DocumentBucket(document)

        bucket_1.title = 'First Title'
        bucket_2.title = 'Second Title'

        assert not bucket_1 == bucket_2

    @pytest.fixture
    def document(self, db_session):
        document = factories.Document()
        db_session.add(document)
        db_session.flush()
        return document


@pytest.mark.usefixtures('factories', 'utcnow')
class TestBucket(object):

    def test_no_annotations(self):
        assert bucketing.bucket([]) == []

    @pytest.mark.parametrize('annotation_datetime,timeframe_label', [
        (FIVE_MINS_AGO, 'Last 7 days'),
        (THIRD_MARCH_1968, 'Mar 1968'),
    ])
    def test_one_annotation(self, annotation_datetime, timeframe_label):
        document = factories.Document()
        results = [factories.Annotation(document=document,
                                        updated=annotation_datetime)]

        timeframes = bucketing.bucket(results)

        assert timeframes == [
            TimeframeMatcher(timeframe_label, {document: results})
        ]

    @pytest.mark.parametrize('annotation_datetime,timeframe_label', [
        (FIVE_MINS_AGO, 'Last 7 days'),
        (THIRD_MARCH_1968, 'Mar 1968'),
    ])
    def test_multiple_annotations_of_one_document_in_one_timeframe(
            self, annotation_datetime, timeframe_label):
        document = factories.Document()
        results = [
            factories.Annotation(document=document,
                                 updated=annotation_datetime)
            for _ in range(3)]

        timeframes = bucketing.bucket(results)

        assert timeframes == [
            TimeframeMatcher(timeframe_label, {document: results}),
        ]

    @pytest.mark.parametrize("annotation_datetime,timeframe_label", [
        (YESTERDAY, "Last 7 days"),
        (THIRD_MARCH_1968, "Mar 1968"),
    ])
    def test_annotations_of_multiple_documents_in_one_timeframe(
            self, annotation_datetime, timeframe_label):
        document_1 = factories.Document()
        document_2 = factories.Document()
        document_3 = factories.Document()
        results = [
            factories.Annotation(document=document_1,
                                 updated=annotation_datetime),
            factories.Annotation(document=document_2,
                                 updated=annotation_datetime),
            factories.Annotation(document=document_3,
                                 updated=annotation_datetime),
        ]

        timeframes = bucketing.bucket(results)

        assert timeframes == [
            TimeframeMatcher(timeframe_label, {
                document_1: [results[0]],
                document_2: [results[1]],
                document_3: [results[2]],
            }),
        ]

    def test_annotations_of_the_same_document_in_different_timeframes(self):
        document = factories.Document()
        results = [
            factories.Annotation(document=document),
            factories.Annotation(document=document,
                                 updated=FIFTH_NOVEMBER_1969),
            factories.Annotation(document=document, updated=THIRD_MARCH_1968),
        ]

        timeframes = bucketing.bucket(results)

        assert timeframes == [
            TimeframeMatcher('Last 7 days', {document: [results[0]]}),
            TimeframeMatcher('Nov 1969', {document: [results[1]]}),
            TimeframeMatcher('Mar 1968', {document: [results[2]]}),
        ]

    def test_recent_and_older_annotations_together(self):
        document_1 = factories.Document()
        document_2 = factories.Document()
        document_3 = factories.Document()
        document_4 = factories.Document()
        document_5 = factories.Document()
        document_6 = factories.Document()
        results = [
            factories.Annotation(document=document_1),
            factories.Annotation(document=document_2),
            factories.Annotation(document=document_3),
            factories.Annotation(document=document_4,
                                 updated=THIRD_MARCH_1968),
            factories.Annotation(document=document_5,
                                 updated=THIRD_MARCH_1968),
            factories.Annotation(document=document_6,
                                 updated=THIRD_MARCH_1968),
        ]

        timeframes = bucketing.bucket(results)

        assert timeframes == [
            TimeframeMatcher('Last 7 days', {
                document_1: [results[0]],
                document_2: [results[1]],
                document_3: [results[2]],
            }),
            TimeframeMatcher('Mar 1968', {
                document_4: [results[3]],
                document_5: [results[4]],
                document_6: [results[5]],
            }),
        ]

    def test_annotations_from_different_days_in_same_month(self):
        """
        Test bucketing multiple annotations from different days of same month.

        Annotations from different days of the same month should go into one
        bucket.

        """
        document = factories.Document()
        one_month_ago = UTCNOW - datetime.timedelta(days=30)
        results = [
            factories.Annotation(document=document, updated=one_month_ago),
            factories.Annotation(document=document,
                        updated=one_month_ago - datetime.timedelta(days=1)),
            factories.Annotation(document=document,
                        updated=one_month_ago - datetime.timedelta(days=2)),
        ]

        timeframes = bucketing.bucket(results)

        assert timeframes == [
            TimeframeMatcher('Jan 1970', {document: results})]


    @pytest.fixture
    def utcnow(self, patch):
        utcnow = patch('h.activity.bucketing.utcnow')
        utcnow.return_value = UTCNOW
        return utcnow
