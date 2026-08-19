from rest_framework import serializers
from .models import CollegeClass, Exam, Semester, Subject, Syllabus, Topic

class SemesterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Semester
        fields = '__all__'
        read_only_fields = ('student',)
    def create(self, validated_data):
        return Semester.objects.create(student=self.context['request'].user, **validated_data)

class SubjectSerializer(serializers.ModelSerializer):
    topic_count = serializers.IntegerField(read_only=True)
    class Meta:
        model = Subject
        fields = '__all__'
    def validate_semester(self, semester):
        if semester.student_id != self.context['request'].user.id:
            raise serializers.ValidationError('Semester does not belong to the authenticated user.')
        return semester

class TopicSerializer(serializers.ModelSerializer):
    class Meta:
        model = Topic
        fields = '__all__'
    def validate_subject(self, subject):
        if subject.semester.student_id != self.context['request'].user.id:
            raise serializers.ValidationError('Subject does not belong to the authenticated user.')
        return subject

class SyllabusSerializer(serializers.ModelSerializer):
    class Meta:
        model = Syllabus
        fields = '__all__'
        read_only_fields = ('uploaded_at', 'created_at', 'updated_at', 'processing_status')
    def validate_semester(self, semester):
        if semester.student_id != self.context['request'].user.id:
            raise serializers.ValidationError('Semester does not belong to the authenticated user.')
        return semester

class ExamSerializer(serializers.ModelSerializer):
    class Meta:
        model = Exam
        fields = '__all__'
    def validate(self, attrs):
        semester = attrs.get('semester', getattr(self.instance, 'semester', None))
        subject = attrs.get('subject', getattr(self.instance, 'subject', None))
        if semester and semester.student_id != self.context['request'].user.id:
            raise serializers.ValidationError({'semester': 'Semester does not belong to the authenticated user.'})
        if semester and subject and subject.semester_id != semester.id:
            raise serializers.ValidationError({'subject': 'Subject must belong to the selected semester.'})
        if attrs.get('end_time', getattr(self.instance, 'end_time', None)) <= attrs.get('start_time', getattr(self.instance, 'start_time', None)):
            raise serializers.ValidationError({'end_time': 'End time must be after start time.'})
        return attrs

class CollegeClassSerializer(serializers.ModelSerializer):
    class Meta:
        model = CollegeClass
        fields = '__all__'
    def validate(self, attrs):
        semester = attrs.get('semester', getattr(self.instance, 'semester', None))
        subject = attrs.get('subject', getattr(self.instance, 'subject', None))
        if semester and semester.student_id != self.context['request'].user.id:
            raise serializers.ValidationError({'semester': 'Semester does not belong to the authenticated user.'})
        if semester and subject and subject.semester_id != semester.id:
            raise serializers.ValidationError({'subject': 'Subject must belong to the selected semester.'})
        if attrs.get('end_time', getattr(self.instance, 'end_time', None)) <= attrs.get('start_time', getattr(self.instance, 'start_time', None)):
            raise serializers.ValidationError({'end_time': 'End time must be after start time.'})
        return attrs
