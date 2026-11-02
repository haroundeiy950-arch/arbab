(() => {
  "use strict";

  const I18N = {
    en: {
      "brand.sub": "Intelligent camera platform",
      "nav.monitoring": "Monitoring",
      "nav.dashboard": "Dashboard",
      "nav.events": "Events",
      "nav.intelligence": "Intelligence",
      "nav.people": "People registry",
      "nav.vehicles": "Vehicle registry",
      "nav.knowledge": "Knowledge base",
      "nav.assistant": "AI assistant",
      "nav.system": "System",
      "nav.settings": "Settings",
      "nav.about": "Safety & limits",
      "status.connecting": "Connecting to alert stream",
      "status.live": "Live alert stream",
      "status.offline": "Alert stream offline",
      "status.reconnecting": "Reconnecting to alerts",
      "topbar.enableSound": "Enable alarm sound",
      "topbar.soundOn": "Alarm sound on",
      "footer.notice": "AI output is advisory. A trained human must verify every alert.",
      "footer.safety": "Safety, privacy & legal notice",
      "alarm.kicker": "Security alert",
      "alarm.title": "Restricted item detected",
      "alarm.hint": "Visual AI detection only. Do not confront anyone. Let trained security staff verify.",
      "alarm.dismiss": "Dismiss alarm",
      "alarm.review": "Review evidence",
      "alarm.soundOn": "Alarm sound enabled",
      "alarm.soundOff": "Alarm sound disabled",
      "common.viewAll": "View all",
      "common.loading": "Loading...",
      "common.openArchive": "Open archive",
      "common.learnMore": "Learn more",
      "common.refresh": "Refresh",
      "common.reset": "Reload",
      "common.cancel": "Cancel",
      "common.save": "Save",
      "common.search": "Search",
      "common.loadMore": "Load more",
      "common.close": "Close",
      "common.delete": "Delete",
      "common.edit": "Edit",
      "common.acknowledge": "Acknowledge",
      "common.acknowledged": "Acknowledged",
      "common.actions": "Actions",
      "common.unknown": "Unknown",
      "common.none": "None",
      "common.error": "Something went wrong",
      "common.saved": "Saved",
      "common.deleted": "Deleted",
      "common.enabled": "Enabled",
      "common.disabled": "Disabled",
      "common.on": "On",
      "common.off": "Off",
      "page.dashboard.title": "Live Dashboard",
      "page.dashboard.subtitle": "AI camera operations overview",
      "page.events.title": "Event Evidence",
      "page.events.subtitle": "Searchable snapshots, clips, speech, and translations",
      "page.people.title": "People Registry",
      "page.people.subtitle": "Consent-based face recognition profiles",
      "page.vehicles.title": "Vehicle Registry",
      "page.vehicles.subtitle": "License plates, vehicles, and owners",
      "page.knowledge.title": "Knowledge Base",
      "page.knowledge.subtitle": "Company documents used by the AI assistant",
      "page.assistant.title": "AI Assistant",
      "page.assistant.subtitle": "Knowledge answers and advisory risk assessment",
      "page.settings.title": "Settings",
      "page.settings.subtitle": "Camera, AI, alerts, audio, and security",
      "page.about.title": "Safety & Limitations",
      "page.about.subtitle": "What this system does, and what it does not do",
      "dash.live": "Live camera",
      "dash.aiOn": "AI on",
      "dash.aiOff": "AI off",
      "dash.audioOn": "Audio on",
      "dash.audioOff": "Audio off",
      "dash.recording": "Recording",
      "dash.liveFeed": "Live feed",
      "dash.demoBadge": "DEMO FEED - NO CAMERA",
      "dash.snapshot": "Save snapshot",
      "dash.startRecording": "Start recording",
      "dash.stopRecording": "Stop recording",
      "dash.riskScan": "Risk inspection",
      "dash.scanPlate": "Read plate",
      "dash.peopleNow": "People now",
      "dash.liveCount": "live count",
      "dash.known": "Registered matches",
      "dash.consentedFaces": "consented faces",
      "dash.unknown": "Unknown faces",
      "dash.unregistered": "unregistered",
      "dash.alerts": "Alerts (24h)",
      "dash.needsReview": "needs review",
      "dash.unique": "Unique people seen",
      "dash.session": "this session",
      "dash.activity": "Interpretation stream",
      "dash.activitySub": "Speech, gestures, plates, and movement translated by AI",
      "dash.localAi": "Local AI",
      "dash.waiting": "Waiting for interpretable activity...",
      "dash.threatMonitor": "Threat monitor",
      "dash.threatSub": "Visible restricted items and risk events",
      "dash.noThreat": "No active threat",
      "dash.noThreatSub": "Monitoring visible items and unknown visitors",
      "dash.activeThreat": "Active security alert",
      "dash.activeThreatSub": "Review the evidence and verify with a human",
      "dash.alarmState": "Alarm system",
      "dash.soundOff": "Sound off",
      "dash.soundOn": "Sound on",
      "dash.recentAlerts": "Recent alerts",
      "dash.recentAlertsSub": "Latest warnings and critical detections",
      "dash.pipeline": "AI pipeline",
      "dash.pipelineSub": "Live service health",
      "dash.pipeObjects": "Object / people tracking",
      "dash.pipePose": "Pose & gestures",
      "dash.pipeFaces": "Face recognition",
      "dash.pipeOcr": "Plate OCR",
      "dash.pipeMic": "Microphone",
      "dash.pipeAgent": "Knowledge agent",
      "dash.lastSpeech": "Last speech",
      "dash.recentEvidence": "Recent evidence",
      "dash.recentEvidenceSub": "Saved snapshots and events from this camera",
      "dash.consentTitle": "Consent and legal notice",
      "dash.consentText": "Face recognition and audio monitoring are lawful only where you have clear legal authority and informed consent where required. Record only areas you are authorized to monitor. AI output is advisory and must be verified by a human. This system does not create nude or body-scan images and does not capture fingerprints.",
      "dash.snapshotSaved": "Snapshot saved to the evidence archive",
      "dash.recordingStarted": "Video recording started",
      "dash.recordingStopped": "Recording stopped and saved",
      "dash.riskDone": "Risk inspection saved",
      "dash.riskNone": "Inspection complete. No restricted visible item was found.",
      "dash.plateRead": "Plate read: {plate}",
      "dash.plateNone": "No plate could be read. Aim at a clear, well-lit plate.",
      "dash.noCamera": "No camera frame is available yet.",
      "dash.ready": "Ready",
      "dash.notReady": "Unavailable",
      "dash.alertCount": "{count} alerts in the last 24 hours",
      "events.heading": "Evidence archive",
      "events.intro": "Every AI alert, translation, speech capture, and manual snapshot is stored with its evidence here.",
      "events.kind": "Event type",
      "events.allKinds": "All types",
      "events.severity": "Severity",
      "events.allSeverities": "All levels",
      "events.apply": "Apply filters",
      "events.clickHint": "Select a card to inspect evidence and translations.",
      "events.none": "No events match these filters.",
      "events.count": "{count} events",
      "events.countMore": "{count}+ events",
      "events.loadFailed": "Could not load events.",
      "events.translation": "Arabic translation",
      "events.original": "Original text",
      "events.english": "English",
      "events.arabic": "Arabic",
      "events.acknowledged": "Event acknowledged",
      "events.deleteConfirm": "Delete this event and all of its evidence files?",
      "kind.threat": "Threat",
      "kind.face_known": "Known face",
      "kind.face_unknown": "Unknown face",
      "kind.speech": "Speech",
      "kind.question": "Question",
      "kind.gesture": "Gesture",
      "kind.plate": "Plate",
      "kind.motion": "Motion",
      "kind.phone": "Phone use",
      "kind.crowd": "Crowd",
      "kind.glasses": "Eyewear",
      "kind.risk_scan": "Risk inspection",
      "kind.snapshot": "Snapshot",
      "kind.inquiry": "Kiosk question",
      "kind.recording": "Recording",
      "severity.critical": "Critical",
      "severity.warning": "Warning",
      "severity.info": "Info",
      "severity.success": "Success",
      "people.heading": "Consent-based people registry",
      "people.intro": "Register people so the camera can display their name and photo when they appear. Only register people who gave informed consent, or where you have a lawful basis.",
      "people.add": "Register person",
      "people.noticeTitle": "No liveness or fingerprint capture",
      "people.noticeText": "This demo uses face embeddings from ordinary photos. It cannot detect presentation attacks reliably and does not scan fingerprints. High-security access control needs certified biometric hardware and a human review process.",
      "people.name": "Full name",
      "people.role": "Role / department",
      "people.company": "Company / organization",
      "people.photo": "Photo",
      "people.notes": "Notes",
      "people.captureNote": "Leave the photo empty to capture the largest face currently in front of the live camera. Upload a clear, front-facing photo for best accuracy.",
      "people.consent": "I confirm this person gave informed consent to local face recognition, or that I have a clear legal basis to register them.",
      "people.consented": "Consent on file",
      "people.submit": "Register face",
      "people.filter": "Filter by name...",
      "people.empty": "No registered people yet. Register only people who consented.",
      "people.count": "{count} registered people",
      "people.registered": "Person registered",
      "people.deleteConfirm": "Delete {name} and their face embedding?",
      "people.photoHint": "No photo",
      "people.consentRequired": "Consent is required before registering a face.",
      "people.notesPlaceholder": "Why this person is registered...",
      "vehicles.heading": "Vehicle registry & plate intelligence",
      "vehicles.intro": "Map a normalized plate to a make, model, and owner. The camera reads plates automatically near detected vehicles and on demand.",
      "vehicles.scanNow": "Read plate now",
      "vehicles.add": "Register vehicle",
      "vehicles.limitTitle": "How make and model matching works",
      "vehicles.limitText": "A plate alone cannot identify a car company or model unless it is linked to a registry. This page is that local registry. For external national registries, configure VEHICLE_LOOKUP_URL in the environment. OCR accuracy depends on lighting, angle, and plate size.",
      "vehicles.lastScan": "Latest plate scan",
      "vehicles.make": "Make",
      "vehicles.model": "Model",
      "vehicles.owner": "Owner",
      "vehicles.confidence": "OCR confidence",
      "vehicles.count": "{count} registered vehicles",
      "vehicles.viewEvidence": "View evidence",
      "vehicles.moderation": "Only authorized operators can edit this registry.",
      "vehicles.plate": "Plate",
      "vehicles.color": "Color",
      "vehicles.notes": "Notes",
      "vehicles.empty": "No vehicles registered yet.",
      "vehicles.deleteConfirm": "Delete vehicle {plate} from the registry?",
      "vehicles.saved": "Vehicle saved",
      "vehicles.registered": "Registered",
      "vehicles.notRegistered": "Not in registry",
      "vehicles.scanDone": "Plate detected: {plate}",
      "vehicles.scanNone": "No plate could be read. Aim the camera at a clear plate.",
      "vehicles.scanFailed": "The plate scan failed.",
      "vehicles.edit": "Edit vehicle",
      "vehicles.addTitle": "Register a vehicle",
      "vehicles.editTitle": "Edit vehicle",
      "knowledge.heading": "Company knowledge base",
      "knowledge.intro": "The AI assistant answers visitor questions only from these documents. Upload Markdown, text, or PDF files. PDFs are searchable but not editable here.",
      "knowledge.upload": "Upload document",
      "knowledge.reindex": "Reindex",
      "knowledge.new": "New document",
      "knowledge.docs": "Documents",
      "knowledge.chunks": "Searchable chunks",
      "knowledge.agent": "Answer provider",
      "knowledge.files": "Documents",
      "knowledge.testSearch": "Test retrieval",
      "knowledge.search": "Search knowledge",
      "knowledge.editor": "Document editor",
      "knowledge.saved": "Saved",
      "knowledge.filename": "File name",
      "knowledge.editorHint": "Markdown is supported. Reindex automatically runs after saving.",
      "knowledge.empty": "No documents yet. Create one to give the assistant company knowledge.",
      "knowledge.unsaved": "Unsaved",
      "knowledge.selectDoc": "Loading document...",
      "knowledge.pdfHint": "PDF documents are searchable but cannot be edited here.",
      "knowledge.newName": "new-document.md",
      "knowledge.savedToast": "Document saved and reindexed",
      "knowledge.uploaded": "Document uploaded and indexed",
      "knowledge.reindexed": "Knowledge reindexed: {count} chunks",
      "knowledge.searchEmpty": "No matching passages. Try different wording.",
      "knowledge.searchResults": "Search results",
      "knowledge.chars": "{count} chars",
      "knowledge.loadFailed": "Could not load this document.",
      "knowledge.saveFailed": "Could not save the document.",
      "knowledge.delete": "Delete document",
      "knowledge.deleteConfirm": "Delete document {name}?",
      "knowledge.uploading": "Uploading...",
      "assistant.heading": "Ask the security agent",
      "assistant.intro": "Questions are answered from the company knowledge base. With an LLM configured, the agent can reason more deeply; without one, it uses local retrieval. A snapshot is saved with each kiosk question.",
      "assistant.agentName": "Sentinel knowledge agent",
      "assistant.agentSub": "Company knowledge - not a general chatbot",
      "assistant.ready": "Ready",
      "assistant.welcomeTitle": "What would you like to know?",
      "assistant.welcomeText": "I can answer questions about the company, meetings, safety policy, and registered vehicles using the documents on the Knowledge page.",
      "assistant.capture": "Save a camera snapshot with this question",
      "assistant.speak": "Speak the answer aloud",
      "assistant.ask": "Ask AI",
      "assistant.assessment": "Risk assessment",
      "assistant.assessmentSub": "AI summary of the last 24 hours",
      "assistant.risk": "RISK",
      "risk.low": "LOW",
      "risk.medium": "MEDIUM",
      "risk.high": "HIGH",
      "assistant.assessHint": "Generate an advisory assessment from recent camera events. A human must verify every conclusion.",
      "assistant.generate": "Generate assessment",
      "assistant.howTitle": "How answers are built",
      "assistant.how1": "The question is matched against company documents using TF-IDF retrieval.",
      "assistant.how2": "An optional OpenAI-compatible model reads the retrieved passages and answers.",
      "assistant.how3": "If the answer is not in the documents, the agent says so instead of inventing facts.",
      "assistant.how4": "Sources are shown with every answer for verification.",
      "assistant.miniNote": "Configure OPENAI_API_KEY or a local OpenAI-compatible endpoint in .env for deeper reasoning.",
      "assistant.placeholder": "Ask about the company...",
      "assistant.thinking": "Searching company knowledge...",
      "assistant.sources": "Sources",
      "assistant.provider": "Provider",
      "assistant.snapshot": "Kiosk snapshot",
      "assistant.answerError": "The assistant could not answer. Try again.",
      "assistant.assessDone": "Assessment generated",
      "assistant.assessError": "Could not generate the assessment.",
      "assistant.assessmentLabel": "Assessment",
      "assistant.you": "You",
      "assistant.agent": "Agent",
      "assistant.saveFirst": "Add at least one document to the knowledge base for grounded answers.",
      "settings.heading": "System configuration",
      "settings.intro": "Tune the camera, AI engines, audio monitoring, alerts, translation, and retention. Changes apply immediately unless marked otherwise.",
      "settings.save": "Save settings",
      "settings.camera": "Camera source",
      "settings.cameraSub": "USB camera index, video file, or RTSP URL",
      "settings.source": "Source",
      "settings.sourceHint": "0 = default webcam. You can also enter a file path or rtsp:// URL. The camera restarts when saved.",
      "settings.width": "Frame width",
      "settings.height": "Frame height",
      "settings.aiEnabled": "AI processing",
      "settings.aiEnabledSub": "Master switch for all computer vision models",
      "settings.vision": "Vision intelligence",
      "settings.visionSub": "People counting, faces, gestures, threats, glasses, and plates",
      "settings.count": "People counting and tracking",
      "settings.countSub": "Live count plus unique visitor IDs during the session",
      "settings.face": "Face recognition",
      "settings.faceSub": "Match consent-based registry faces only",
      "settings.faceThreshold": "Face match threshold",
      "settings.personConf": "Person confidence",
      "settings.interval": "AI analysis interval (seconds)",
      "settings.gesture": "Gesture and sign interpretation",
      "settings.gestureSub": "Wave, raised hand, stop, welcome, yes, and no from pose",
      "settings.plate": "License plate recognition",
      "settings.plateSub": "Plate OCR plus local vehicle registry lookup",
      "settings.threat": "Restricted visible items",
      "settings.threatSub": "COCO knife/scissors/bat plus optional custom weapon model",
      "settings.restricted": "Restricted classes (comma separated)",
      "settings.glasses": "Eyewear classification",
      "settings.glassesHint": "Heuristic only. It cannot prove that glasses contain a camera.",
      "settings.smartGlasses": "Warn on possible smart glasses",
      "settings.smartGlassesSub": "Advisory warning only, never a weapon alarm",
      "settings.privacyBlur": "Blur unknown faces in the live view",
      "settings.privacyBlurSub": "Evidence snapshots remain unblurred for authorized review",
      "settings.alerts": "Alerts & evidence",
      "settings.alertsSub": "Siren, automatic snapshots, motion clips, and retention",
      "settings.alarm": "Loud alarm on critical detections",
      "settings.alarmSub": "Browser siren and spoken warning with person name and item",
      "settings.unknownAlert": "Alert on unknown faces",
      "settings.unknownAlertSub": "Save a warning when a face is not in the registry",
      "settings.motion": "Save meaningful motion snapshots",
      "settings.motionSub": "Frame-difference motion with snapshot evidence",
      "settings.motionThreshold": "Motion threshold",
      "settings.retention": "Evidence retention (days)",
      "settings.riskScan": "Privacy-safe risk inspection",
      "settings.riskScanHint": "Blurred bodies, visible items only. No body scan or nudity generation.",
      "settings.audio": "Audio, speech & translation",
      "settings.audioSub": "Microphone monitoring, Whisper transcription, and AI translation",
      "settings.audioOn": "Microphone monitoring",
      "settings.audioOnSub": "Record speech when sound is detected. Requires consent and legal approval.",
      "settings.transcribe": "Transcribe speech with Whisper",
      "settings.transcribeSub": "Local CPU transcription; first use downloads the model",
      "settings.translate": "Translate events and speech",
      "settings.translateSub": "Arabic and English translations attached to evidence",
      "settings.autoAnswer": "Answer spoken questions automatically",
      "settings.autoAnswerSub": "Transcribed questions are answered from company knowledge and spoken by the dashboard",
      "settings.audioThreshold": "Voice threshold (RMS)",
      "settings.targets": "Translation targets",
      "settings.notificationLanguage": "Notification language",
      "settings.organization": "Organization & assistant",
      "settings.organizationSub": "Company name used in the knowledge base and greeting",
      "settings.company": "Company name",
      "settings.llm": "Agent provider",
      "settings.llmHint": "Set OPENAI_API_KEY / OPENAI_BASE_URL / OPENAI_MODEL in .env to enable deeper answers.",
      "settings.security": "Security",
      "settings.securitySub": "Change the administrator password",
      "settings.currentPassword": "Current password",
      "settings.newPassword": "New password",
      "settings.confirmPassword": "Confirm new password",
      "settings.changePassword": "Change password",
      "settings.maintenance": "Maintenance",
      "settings.maintenanceSub": "Model health and evidence retention",
      "settings.cleanup": "Run retention cleanup",
      "settings.envNote": "Secrets and model endpoints are configured in the .env file, not in this page. Restart the app after changing them.",
      "settings.saved": "Settings saved",
      "settings.reloaded": "Settings reloaded",
      "settings.saveFailed": "Could not save settings.",
      "settings.passwordChanged": "Password changed",
      "settings.passwordMismatch": "The new passwords do not match.",
      "settings.passwordShort": "Use at least 10 characters.",
      "settings.cleanupDone": "Retention cleanup removed {count} events",
      "settings.modelObjects": "Object model",
      "settings.modelPose": "Pose model",
      "settings.modelFaces": "Face models",
      "settings.modelPlates": "Plate OCR",
      "settings.modelThreats": "Custom threat model",
      "settings.operational": "Ready",
      "settings.missing": "Missing",
      "settings.providerLocal": "Built-in local retrieval",
      "settings.providerOpenAI": "OpenAI-compatible model",
      "settings.modelHealth": "Model health",
      "settings.cleanupFailed": "Cleanup failed.",
      "detail.title": "Event details",
      "detail.kind": "Type",
      "detail.severity": "Severity",
      "detail.person": "Person",
      "detail.time": "Time",
      "detail.status": "Status",
      "detail.acknowledged": "Acknowledged",
      "detail.pending": "Needs review",
      "detail.description": "Description",
      "detail.arabicTranslation": "Arabic translation",
      "detail.englishOriginal": "English original",
      "detail.transcript": "Transcript",
      "detail.translation": "Translation",
      "detail.audio": "Audio evidence",
      "detail.video": "Video evidence",
      "detail.snapshot": "Snapshot evidence",
      "detail.sources": "Sources",
      "detail.provider": "Provider",
      "detail.item": "Detected item",
      "detail.confidence": "Confidence",
      "detail.plate": "Plate",
      "detail.noEvidence": "No media evidence was attached to this event.",
      "detail.deleteConfirm": "Delete this event and all evidence files?",
      "detail.deleted": "Event deleted",
      "detail.acknowledgedToast": "Event acknowledged",
      "detail.actionFailed": "The action failed.",
      "detail.metadata": "Additional data",
      "detail.language": "Language",
      "detail.gesture": "Gesture",
      "detail.riskFindings": "Visible findings",
      "detail.registered": "Registered",
      "detail.notRegistered": "Unregistered",
      "detail.loading": "Loading event..."
    },
    ar: {
      "brand.sub": "منصة كاميرا ذكية",
      "nav.monitoring": "المراقبة",
      "nav.dashboard": "لوحة التحكم",
      "nav.events": "الأحداث",
      "nav.intelligence": "الذكاء الاصطناعي",
      "nav.people": "سجل الأشخاص",
      "nav.vehicles": "سجل المركبات",
      "nav.knowledge": "قاعدة المعرفة",
      "nav.assistant": "المساعد الذكي",
      "nav.system": "النظام",
      "nav.settings": "الإعدادات",
      "nav.about": "السلامة والحدود",
      "status.connecting": "جارٍ الاتصال ببث التنبيهات",
      "status.live": "بث التنبيهات متصل",
      "status.offline": "بث التنبيهات غير متصل",
      "status.reconnecting": "إعادة الاتصال بالتنبيهات",
      "topbar.enableSound": "تفعيل صوت الإنذار",
      "topbar.soundOn": "صوت الإنذار مفعّل",
      "footer.notice": "مخرجات الذكاء الاصطناعي استشارية. يجب أن يتحقق إنسان مدرب من كل تنبيه.",
      "footer.safety": "إشعار السلامة والخصوصية والقانون",
      "alarm.kicker": "تنبيه أمني",
      "alarm.title": "تم اكتشاف عنصر محظور",
      "alarm.hint": "اكتشاف بصري بالذكاء الاصطناعي فقط. لا تواجه أي شخص. دع أفراد الأمن المدربين يتحققون.",
      "alarm.dismiss": "إغلاق الإنذار",
      "alarm.review": "مراجعة الأدلة",
      "alarm.soundOn": "تم تفعيل صوت الإنذار",
      "alarm.soundOff": "تم إيقاف صوت الإنذار",
      "common.viewAll": "عرض الكل",
      "common.loading": "جارٍ التحميل...",
      "common.openArchive": "فتح الأرشيف",
      "common.learnMore": "اعرف المزيد",
      "common.refresh": "تحديث",
      "common.reset": "إعادة تحميل",
      "common.cancel": "إلغاء",
      "common.save": "حفظ",
      "common.search": "بحث",
      "common.loadMore": "تحميل المزيد",
      "common.close": "إغلاق",
      "common.delete": "حذف",
      "common.edit": "تعديل",
      "common.acknowledge": "تأكيد المراجعة",
      "common.acknowledged": "تمت المراجعة",
      "common.actions": "الإجراءات",
      "common.unknown": "غير معروف",
      "common.none": "لا يوجد",
      "common.error": "حدث خطأ ما",
      "common.saved": "تم الحفظ",
      "common.deleted": "تم الحذف",
      "common.enabled": "مفعّل",
      "common.disabled": "متوقف",
      "common.on": "مفعّل",
      "common.off": "متوقف",
      "page.dashboard.title": "لوحة المراقبة المباشرة",
      "page.dashboard.subtitle": "نظرة عامة على تشغيل الكاميرا الذكية",
      "page.events.title": "أرشيف الأدلة",
      "page.events.subtitle": "لقطات ومقاطع وكلام وترجمات قابلة للبحث",
      "page.people.title": "سجل الأشخاص",
      "page.people.subtitle": "ملفات التعرف على الوجوه القائمة على الموافقة",
      "page.vehicles.title": "سجل المركبات",
      "page.vehicles.subtitle": "لوحات المركبات والمالكون",
      "page.knowledge.title": "قاعدة المعرفة",
      "page.knowledge.subtitle": "مستندات الشركة المستخدمة من المساعد الذكي",
      "page.assistant.title": "المساعد الذكي",
      "page.assistant.subtitle": "إجابات معرفية وتقييم مخاطر استشاري",
      "page.settings.title": "الإعدادات",
      "page.settings.subtitle": "الكاميرا والذكاء الاصطناعي والتنبيهات والصوت والأمان",
      "page.about.title": "السلامة والحدود",
      "page.about.subtitle": "ما يفعله هذا النظام وما لا يفعله",
      "dash.live": "الكاميرا المباشرة",
      "dash.aiOn": "الذكاء مفعّل",
      "dash.aiOff": "الذكاء متوقف",
      "dash.audioOn": "الصوت مفعّل",
      "dash.audioOff": "الصوت متوقف",
      "dash.recording": "جارٍ التسجيل",
      "dash.liveFeed": "بث مباشر",
      "dash.demoBadge": "بث تجريبي - لا توجد كاميرا",
      "dash.snapshot": "حفظ لقطة",
      "dash.startRecording": "بدء التسجيل",
      "dash.stopRecording": "إيقاف التسجيل",
      "dash.riskScan": "فحص المخاطر",
      "dash.scanPlate": "قراءة اللوحة",
      "dash.peopleNow": "الأشخاص الآن",
      "dash.liveCount": "العدد المباشر",
      "dash.known": "المطابقات المسجلة",
      "dash.consentedFaces": "وجوه بموافقة",
      "dash.unknown": "وجوه غير معروفة",
      "dash.unregistered": "غير مسجلة",
      "dash.alerts": "التنبيهات (٢٤ ساعة)",
      "dash.needsReview": "تحتاج مراجعة",
      "dash.unique": "أشخاص مميزون",
      "dash.session": "هذه الجلسة",
      "dash.activity": "بث التفسير",
      "dash.activitySub": "كلام وإيماءات ولوحات وحركة يترجمها الذكاء الاصطناعي",
      "dash.localAi": "ذكاء محلي",
      "dash.waiting": "في انتظار نشاط قابل للتفسير...",
      "dash.threatMonitor": "مراقب التهديدات",
      "dash.threatSub": "العناصر المحظورة الظاهرة وأحداث المخاطر",
      "dash.noThreat": "لا يوجد تهديد نشط",
      "dash.noThreatSub": "مراقبة العناصر الظاهرة والزوار غير المعروفين",
      "dash.activeThreat": "تنبيه أمني نشط",
      "dash.activeThreatSub": "راجع الأدلة وتحقق بشرياً",
      "dash.alarmState": "نظام الإنذار",
      "dash.soundOff": "الصوت متوقف",
      "dash.soundOn": "الصوت مفعّل",
      "dash.recentAlerts": "التنبيهات الأخيرة",
      "dash.recentAlertsSub": "أحدث التحذيرات والاكتشافات الحرجة",
      "dash.pipeline": "مسار الذكاء الاصطناعي",
      "dash.pipelineSub": "حالة الخدمات المباشرة",
      "dash.pipeObjects": "تتبع الأشياء والأشخاص",
      "dash.pipePose": "الوضعيات والإيماءات",
      "dash.pipeFaces": "التعرف على الوجوه",
      "dash.pipeOcr": "قراءة اللوحات",
      "dash.pipeMic": "الميكروفون",
      "dash.pipeAgent": "وكيل المعرفة",
      "dash.lastSpeech": "آخر كلام",
      "dash.recentEvidence": "الأدلة الأخيرة",
      "dash.recentEvidenceSub": "لقطات وأحداث محفوظة من هذه الكاميرا",
      "dash.consentTitle": "الموافقة والإشعار القانوني",
      "dash.consentText": "التعرف على الوجوه ومراقبة الصوت قانونيان فقط عند وجود صلاحية قانونية واضحة وموافقة مستنيرة حيث تلزم. سجّل المناطق المصرح بمراقبتها فقط. مخرجات الذكاء الاصطناعي استشارية ويجب أن يتحقق منها إنسان. لا ينشئ هذا النظام صوراً عارية أو فحوصاً للجسم ولا يلتقط بصمات.",
      "dash.snapshotSaved": "تم حفظ اللقطة في أرشيف الأدلة",
      "dash.recordingStarted": "بدأ تسجيل الفيديو",
      "dash.recordingStopped": "تم إيقاف التسجيل وحفظه",
      "dash.riskDone": "تم حفظ فحص المخاطر",
      "dash.riskNone": "اكتمل الفحص. لم يُعثر على عنصر محظور ظاهر.",
      "dash.plateRead": "تمت قراءة اللوحة: {plate}",
      "dash.plateNone": "تعذر قراءة اللوحة. وجّه الكاميرا نحو لوحة واضحة ومضاءة.",
      "dash.noCamera": "لا تتوفر صورة كاميرا بعد.",
      "dash.ready": "جاهز",
      "dash.notReady": "غير متاح",
      "dash.alertCount": "{count} تنبيه خلال آخر ٢٤ ساعة",
      "events.heading": "أرشيف الأدلة",
      "events.intro": "كل تنبيه ذكاء اصطناعي وترجمة والتقاط كلام ولقطة يدوية يُحفظ مع دليله هنا.",
      "events.kind": "نوع الحدث",
      "events.allKinds": "كل الأنواع",
      "events.severity": "الخطورة",
      "events.allSeverities": "كل المستويات",
      "events.apply": "تطبيق الفلاتر",
      "events.clickHint": "اختر بطاقة لفحص الدليل والترجمات.",
      "events.none": "لا توجد أحداث مطابقة لهذه الفلاتر.",
      "events.count": "{count} حدث",
      "events.countMore": "أكثر من {count} حدث",
      "events.loadFailed": "تعذر تحميل الأحداث.",
      "events.translation": "الترجمة العربية",
      "events.original": "النص الأصلي",
      "events.english": "الإنجليزية",
      "events.arabic": "العربية",
      "events.acknowledged": "تمت مراجعة الحدث",
      "events.deleteConfirm": "حذف هذا الحدث وكل ملفات أدلته؟",
      "kind.threat": "تهديد",
      "kind.face_known": "وجه معروف",
      "kind.face_unknown": "وجه غير معروف",
      "kind.speech": "كلام",
      "kind.question": "سؤال",
      "kind.gesture": "إيماءة",
      "kind.plate": "لوحة",
      "kind.motion": "حركة",
      "kind.phone": "استخدام الهاتف",
      "kind.crowd": "ازدحام",
      "kind.glasses": "نظارات",
      "kind.risk_scan": "فحص مخاطر",
      "kind.snapshot": "لقطة",
      "kind.inquiry": "سؤال كشك",
      "kind.recording": "تسجيل",
      "severity.critical": "حرج",
      "severity.warning": "تحذير",
      "severity.info": "معلومة",
      "severity.success": "نجاح",
      "people.heading": "سجل أشخاص قائم على الموافقة",
      "people.intro": "سجّل الأشخاص لتتمكن الكاميرا من عرض اسمهم وصورتهم عند ظهورهم. سجّل فقط من أعطى موافقة مستنيرة، أو من لديك أساس قانوني لتسجيله.",
      "people.add": "تسجيل شخص",
      "people.noticeTitle": "لا كشف حياة ولا التقاط بصمات",
      "people.noticeText": "يستخدم هذا العرض بصمات وجه من صور عادية. لا يمكنه كشف محاولات الانتحال بشكل موثوق ولا يمسح البصمات. التحكم الأمني العالي يحتاج أجهزة معتمدة ومراجعة بشرية.",
      "people.name": "الاسم الكامل",
      "people.role": "الدور / القسم",
      "people.company": "الشركة / المؤسسة",
      "people.photo": "الصورة",
      "people.notes": "ملاحظات",
      "people.captureNote": "اترك الصورة فارغة لالتقاط أكبر وجه أمام الكاميرا المباشرة. ارفع صورة واضحة أمامية لأفضل دقة.",
      "people.consent": "أؤكد أن هذا الشخص أعطى موافقة مستنيرة للتعرف المحلي على الوجه، أو أن لدي أساساً قانونياً واضحاً لتسجيله.",
      "people.consented": "الموافقة محفوظة",
      "people.submit": "تسجيل الوجه",
      "people.filter": "تصفية بالاسم...",
      "people.empty": "لا يوجد أشخاص مسجلون بعد. سجّل فقط من وافقوا.",
      "people.count": "{count} شخصاً مسجلاً",
      "people.registered": "تم تسجيل الشخص",
      "people.deleteConfirm": "حذف {name} وبصمة وجهه؟",
      "people.photoHint": "لا توجد صورة",
      "people.consentRequired": "الموافقة مطلوبة قبل تسجيل الوجه.",
      "people.notesPlaceholder": "سبب تسجيل هذا الشخص...",
      "vehicles.heading": "سجل المركبات وذكاء اللوحات",
      "vehicles.intro": "اربط لوحة موحدة بالشركة والطراز والمالك. تقرأ الكاميرا اللوحات تلقائياً قرب المركبات المكتشفة وعند الطلب.",
      "vehicles.scanNow": "قراءة اللوحة الآن",
      "vehicles.add": "تسجيل مركبة",
      "vehicles.limitTitle": "كيف تعمل مطابقة الشركة والطراز",
      "vehicles.limitText": "لا يمكن للوحة وحدها تحديد الشركة أو الطراز ما لم تكن مرتبطة بسجل. هذه الصفحة هي السجل المحلي. للسجلات الوطنية الخارجية اضبط VEHICLE_LOOKUP_URL. تعتمد دقة القراءة على الإضاءة والزاوية وحجم اللوحة.",
      "vehicles.lastScan": "أحدث قراءة لوحة",
      "vehicles.make": "الشركة",
      "vehicles.model": "الطراز",
      "vehicles.owner": "المالك",
      "vehicles.confidence": "ثقة القراءة",
      "vehicles.count": "{count} مركبة مسجلة",
      "vehicles.viewEvidence": "عرض الدليل",
      "vehicles.moderation": "يمكن للمشغلين المصرح لهم فقط تعديل هذا السجل.",
      "vehicles.plate": "اللوحة",
      "vehicles.color": "اللون",
      "vehicles.notes": "ملاحظات",
      "vehicles.empty": "لا توجد مركبات مسجلة بعد.",
      "vehicles.deleteConfirm": "حذف المركبة {plate} من السجل؟",
      "vehicles.saved": "تم حفظ المركبة",
      "vehicles.registered": "مسجلة",
      "vehicles.notRegistered": "غير موجودة في السجل",
      "vehicles.scanDone": "تم اكتشاف اللوحة: {plate}",
      "vehicles.scanNone": "تعذر قراءة اللوحة. وجّه الكاميرا نحو لوحة واضحة.",
      "vehicles.scanFailed": "فشلت قراءة اللوحة.",
      "vehicles.edit": "تعديل المركبة",
      "vehicles.addTitle": "تسجيل مركبة",
      "vehicles.editTitle": "تعديل مركبة",
      "knowledge.heading": "قاعدة معرفة الشركة",
      "knowledge.intro": "يجيب المساعد الذكي على أسئلة الزوار من هذه المستندات فقط. ارفع ملفات Markdown أو نص أو PDF. ملفات PDF قابلة للبحث لكن غير قابلة للتحرير هنا.",
      "knowledge.upload": "رفع مستند",
      "knowledge.reindex": "إعادة الفهرسة",
      "knowledge.new": "مستند جديد",
      "knowledge.docs": "المستندات",
      "knowledge.chunks": "أجزاء قابلة للبحث",
      "knowledge.agent": "مزود الإجابات",
      "knowledge.files": "المستندات",
      "knowledge.testSearch": "اختبار الاسترجاع",
      "knowledge.search": "البحث في المعرفة",
      "knowledge.editor": "محرر المستند",
      "knowledge.saved": "محفوظ",
      "knowledge.filename": "اسم الملف",
      "knowledge.editorHint": "يدعم Markdown. تُعاد الفهرسة تلقائياً بعد الحفظ.",
      "knowledge.empty": "لا توجد مستندات. أنشئ مستنداً لتزويد المساعد بمعرفة الشركة.",
      "knowledge.unsaved": "غير محفوظ",
      "knowledge.selectDoc": "جارٍ تحميل المستند...",
      "knowledge.pdfHint": "مستندات PDF قابلة للبحث لكن لا يمكن تحريرها هنا.",
      "knowledge.newName": "new-document.md",
      "knowledge.savedToast": "تم حفظ المستند وإعادة فهرسته",
      "knowledge.uploaded": "تم رفع المستند وفهرسته",
      "knowledge.reindexed": "تمت إعادة فهرسة المعرفة: {count} جزء",
      "knowledge.searchEmpty": "لا توجد فقرات مطابقة. جرّب صياغة أخرى.",
      "knowledge.searchResults": "نتائج البحث",
      "knowledge.chars": "{count} حرفاً",
      "knowledge.loadFailed": "تعذر تحميل هذا المستند.",
      "knowledge.saveFailed": "تعذر حفظ المستند.",
      "knowledge.delete": "حذف المستند",
      "knowledge.deleteConfirm": "حذف المستند {name}؟",
      "knowledge.uploading": "جارٍ الرفع...",
      "assistant.heading": "اسأل وكيل الأمن",
      "assistant.intro": "تُجاب الأسئلة من قاعدة معرفة الشركة. عند إعداد نموذج لغوي يمكن للوكيل التفكير بعمق أكبر؛ وبدونه يستخدم الاسترجاع المحلي. تُحفظ لقطة مع كل سؤال كشك.",
      "assistant.agentName": "وكيل معرفة Sentinel",
      "assistant.agentSub": "معرفة الشركة - ليس روبوت دردشة عاماً",
      "assistant.ready": "جاهز",
      "assistant.welcomeTitle": "ماذا تريد أن تعرف؟",
      "assistant.welcomeText": "أستطيع الإجابة عن أسئلة الشركة والاجتماعات وسياسة السلامة والمركبات المسجلة باستخدام مستندات صفحة المعرفة.",
      "assistant.capture": "حفظ لقطة كاميرا مع هذا السؤال",
      "assistant.speak": "نطق الإجابة بصوت عالٍ",
      "assistant.ask": "اسأل الذكاء الاصطناعي",
      "assistant.assessment": "تقييم المخاطر",
      "assistant.assessmentSub": "ملخص ذكي لآخر ٢٤ ساعة",
      "assistant.risk": "المخاطر",
      "risk.low": "منخفض",
      "risk.medium": "متوسط",
      "risk.high": "مرتفع",
      "assistant.assessHint": "أنشئ تقييماً استشارياً من أحداث الكاميرا الأخيرة. يجب أن يتحقق إنسان من كل استنتاج.",
      "assistant.generate": "إنشاء التقييم",
      "assistant.howTitle": "كيف تُبنى الإجابات",
      "assistant.how1": "تتم مطابقة السؤال مع مستندات الشركة باستخدام استرجاع TF-IDF.",
      "assistant.how2": "يمكن لنموذج متوافق مع OpenAI قراءة الفقرات المسترجعة والإجابة.",
      "assistant.how3": "إذا لم تكن الإجابة في المستندات يقول الوكيل ذلك بدلاً من اختراع الحقائق.",
      "assistant.how4": "تُعرض المصادر مع كل إجابة للتحقق.",
      "assistant.miniNote": "اضبط OPENAI_API_KEY أو نقطة نهاية محلية متوافقة مع OpenAI في .env لتفكير أعمق.",
      "assistant.placeholder": "اسأل عن الشركة...",
      "assistant.thinking": "جارٍ البحث في معرفة الشركة...",
      "assistant.sources": "المصادر",
      "assistant.provider": "المزود",
      "assistant.snapshot": "لقطة الكشك",
      "assistant.answerError": "تعذر على المساعد الإجابة. حاول مرة أخرى.",
      "assistant.assessDone": "تم إنشاء التقييم",
      "assistant.assessError": "تعذر إنشاء التقييم.",
      "assistant.assessmentLabel": "التقييم",
      "assistant.you": "أنت",
      "assistant.agent": "الوكيل",
      "assistant.saveFirst": "أضف مستنداً واحداً على الأقل إلى قاعدة المعرفة لإجابات موثقة.",
      "settings.heading": "إعدادات النظام",
      "settings.intro": "اضبط الكاميرا ومحركات الذكاء والصوت والتنبيهات والترجمة والاحتفاظ. تُطبق التغييرات فوراً ما لم يُذكر خلاف ذلك.",
      "settings.save": "حفظ الإعدادات",
      "settings.camera": "مصدر الكاميرا",
      "settings.cameraSub": "رقم كاميرا USB أو ملف فيديو أو رابط RTSP",
      "settings.source": "المصدر",
      "settings.sourceHint": "0 = كاميرا الويب الافتراضية. يمكنك إدخال مسار ملف أو رابط rtsp://. تُعاد الكاميرا عند الحفظ.",
      "settings.width": "عرض الإطار",
      "settings.height": "ارتفاع الإطار",
      "settings.aiEnabled": "معالجة الذكاء الاصطناعي",
      "settings.aiEnabledSub": "المفتاح الرئيسي لكل نماذج الرؤية الحاسوبية",
      "settings.vision": "ذكاء الرؤية",
      "settings.visionSub": "عدّ الأشخاص والوجوه والإيماءات والتهديدات والنظارات واللوحات",
      "settings.count": "عدّ الأشخاص وتتبعهم",
      "settings.countSub": "عدد مباشر ومعرفات زوار مميزة خلال الجلسة",
      "settings.face": "التعرف على الوجوه",
      "settings.faceSub": "مطابقة وجوه السجل القائمة على الموافقة فقط",
      "settings.faceThreshold": "عتبة مطابقة الوجه",
      "settings.personConf": "ثقة كشف الشخص",
      "settings.interval": "فاصل تحليل الذكاء (ثوانٍ)",
      "settings.gesture": "تفسير الإيماءات والإشارات",
      "settings.gestureSub": "تلويح ورفع يد وتوقف وترحيب ونعم ولا من الوضعية",
      "settings.plate": "التعرف على لوحات المركبات",
      "settings.plateSub": "قراءة اللوحة والبحث في سجل المركبات المحلي",
      "settings.threat": "العناصر المحظورة الظاهرة",
      "settings.threatSub": "سكين/مقص/مضرب COCO ونموذج أسلحة مخصص اختياري",
      "settings.restricted": "الفئات المحظورة (مفصولة بفواصل)",
      "settings.glasses": "تصنيف النظارات",
      "settings.glassesHint": "تقريبي فقط. لا يمكنه إثبات وجود كاميرا في النظارة.",
      "settings.smartGlasses": "تحذير عند احتمال نظارة ذكية",
      "settings.smartGlassesSub": "تحذير استشاري فقط، وليس إنذار سلاح",
      "settings.privacyBlur": "تمويه الوجوه غير المعروفة في العرض المباشر",
      "settings.privacyBlurSub": "تبقى لقطات الأدلة دون تمويه للمراجعة المصرح بها",
      "settings.alerts": "التنبيهات والأدلة",
      "settings.alertsSub": "صافرة ولقطات تلقائية ومقاطع حركة واحتفاظ",
      "settings.alarm": "إنذار عالٍ عند الاكتشافات الحرجة",
      "settings.alarmSub": "صافرة المتصفح وتحذير منطوق باسم الشخص والعنصر",
      "settings.unknownAlert": "التنبيه عند الوجوه غير المعروفة",
      "settings.unknownAlertSub": "حفظ تحذير عندما لا يكون الوجه في السجل",
      "settings.motion": "حفظ لقطات الحركة ذات المعنى",
      "settings.motionSub": "حركة بفارق الإطارات مع لقطة دليل",
      "settings.motionThreshold": "عتبة الحركة",
      "settings.retention": "الاحتفاظ بالأدلة (أيام)",
      "settings.riskScan": "فحص مخاطر يحمي الخصوصية",
      "settings.riskScanHint": "أجساد مموهة وعناصر ظاهرة فقط. لا فحص جسم ولا توليد صور عارية.",
      "settings.audio": "الصوت والكلام والترجمة",
      "settings.audioSub": "مراقبة الميكروفون ونسخ Whisper وترجمة الذكاء الاصطناعي",
      "settings.audioOn": "مراقبة الميكروفون",
      "settings.audioOnSub": "تسجيل الكلام عند اكتشاف صوت. يتطلب موافقة وموافقة قانونية.",
      "settings.transcribe": "نسخ الكلام باستخدام Whisper",
      "settings.transcribeSub": "نسخ محلي على المعالج؛ أول استخدام ينزّل النموذج",
      "settings.translate": "ترجمة الأحداث والكلام",
      "settings.translateSub": "ترجمات عربية وإنجليزية مرفقة بالأدلة",
      "settings.autoAnswer": "الإجابة عن الأسئلة المنطوقة تلقائياً",
      "settings.autoAnswerSub": "تُجاب الأسئلة المنسوخة من معرفة الشركة وينطقها لوح التحكم",
      "settings.audioThreshold": "عتبة الصوت (RMS)",
      "settings.targets": "أهداف الترجمة",
      "settings.notificationLanguage": "لغة التنبيهات",
      "settings.organization": "المؤسسة والمساعد",
      "settings.organizationSub": "اسم الشركة المستخدم في قاعدة المعرفة والترحيب",
      "settings.company": "اسم الشركة",
      "settings.llm": "مزود الوكيل",
      "settings.llmHint": "اضبط OPENAI_API_KEY / OPENAI_BASE_URL / OPENAI_MODEL في .env لتمكين إجابات أعمق.",
      "settings.security": "الأمان",
      "settings.securitySub": "تغيير كلمة مرور المسؤول",
      "settings.currentPassword": "كلمة المرور الحالية",
      "settings.newPassword": "كلمة المرور الجديدة",
      "settings.confirmPassword": "تأكيد كلمة المرور الجديدة",
      "settings.changePassword": "تغيير كلمة المرور",
      "settings.maintenance": "الصيانة",
      "settings.maintenanceSub": "سلامة النماذج والاحتفاظ بالأدلة",
      "settings.cleanup": "تشغيل تنظيف الاحتفاظ",
      "settings.envNote": "تُضبط الأسرار ونقاط نهاية النماذج في ملف .env وليس هنا. أعد تشغيل التطبيق بعد تغييرها.",
      "settings.saved": "تم حفظ الإعدادات",
      "settings.reloaded": "تم إعادة تحميل الإعدادات",
      "settings.saveFailed": "تعذر حفظ الإعدادات.",
      "settings.passwordChanged": "تم تغيير كلمة المرور",
      "settings.passwordMismatch": "كلمتا المرور الجديدتان غير متطابقتين.",
      "settings.passwordShort": "استخدم ١٠ أحرف على الأقل.",
      "settings.cleanupDone": "أزال تنظيف الاحتفاظ {count} حدثاً",
      "settings.modelObjects": "نموذج الأشياء",
      "settings.modelPose": "نموذج الوضعية",
      "settings.modelFaces": "نماذج الوجوه",
      "settings.modelPlates": "قراءة اللوحات",
      "settings.modelThreats": "نموذج التهديدات المخصص",
      "settings.operational": "جاهز",
      "settings.missing": "مفقود",
      "settings.providerLocal": "استرجاع محلي مدمج",
      "settings.providerOpenAI": "نموذج متوافق مع OpenAI",
      "settings.modelHealth": "سلامة النماذج",
      "settings.cleanupFailed": "فشل التنظيف.",
      "detail.title": "تفاصيل الحدث",
      "detail.kind": "النوع",
      "detail.severity": "الخطورة",
      "detail.person": "الشخص",
      "detail.time": "الوقت",
      "detail.status": "الحالة",
      "detail.acknowledged": "تمت المراجعة",
      "detail.pending": "تحتاج مراجعة",
      "detail.description": "الوصف",
      "detail.arabicTranslation": "الترجمة العربية",
      "detail.englishOriginal": "النص الإنجليزي الأصلي",
      "detail.transcript": "النص المنسوخ",
      "detail.translation": "الترجمة",
      "detail.audio": "دليل صوتي",
      "detail.video": "دليل فيديو",
      "detail.snapshot": "دليل لقطة",
      "detail.sources": "المصادر",
      "detail.provider": "المزود",
      "detail.item": "العنصر المكتشف",
      "detail.confidence": "الثقة",
      "detail.plate": "اللوحة",
      "detail.noEvidence": "لم يُرفق أي دليل وسائط بهذا الحدث.",
      "detail.deleteConfirm": "حذف هذا الحدث وكل ملفات الأدلة؟",
      "detail.deleted": "تم حذف الحدث",
      "detail.acknowledgedToast": "تمت مراجعة الحدث",
      "detail.actionFailed": "فشل الإجراء.",
      "detail.metadata": "بيانات إضافية",
      "detail.language": "اللغة",
      "detail.gesture": "الإيماءة",
      "detail.riskFindings": "العناصر الظاهرة",
      "detail.registered": "مسجلة",
      "detail.notRegistered": "غير مسجلة",
      "detail.loading": "جارٍ تحميل الحدث..."
    }
  };

  const state = {
    lang: "en",
    sound: false,
    wantedSound: false,
    audioCtx: null,
    sirenTimer: null,
    sirenStopTimer: null,
    ws: null,
    wsConnected: false,
    wsRetry: 1000,
    wsTimer: null,
    pingTimer: null,
    listeners: new Set(),
    lastAlarmId: null,
    lastSpeech: { text: "", at: 0 }
  };

  const $ = (selector, root = document) => root.querySelector(selector);
  const $$ = (selector, root = document) => Array.from(root.querySelectorAll(selector));

  function t(key, vars = {}) {
    const table = I18N[state.lang] || I18N.en;
    let text = table[key] ?? I18N.en[key] ?? key;
    Object.keys(vars).forEach((name) => {
      text = text.replaceAll(`{${name}}`, String(vars[name]));
    });
    return text;
  }

  function escapeHtml(value) {
    return String(value ?? "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#39;");
  }

  function safeUrl(value) {
    const raw = String(value ?? "").trim();
    if (!raw) return "";
    if (raw.startsWith("/") || raw.startsWith("http://") || raw.startsWith("https://") || raw.startsWith("data:image/")) {
      return raw;
    }
    return "";
  }

  function api(path, options = {}) {
    const opts = { credentials: "same-origin", ...options };
    const headers = { Accept: "application/json", ...(options.headers || {}) };
    if (opts.body !== undefined && opts.body !== null && !(opts.body instanceof FormData) && typeof opts.body !== "string") {
      headers["Content-Type"] = "application/json";
      opts.body = JSON.stringify(opts.body);
    }
    opts.headers = headers;
    return fetch(path, opts).then(async (response) => {
      if (response.status === 401) {
        window.location.href = "/login";
        throw new Error("Authentication required");
      }
      const type = response.headers.get("content-type") || "";
      let data = null;
      if (type.includes("application/json")) {
        data = await response.json().catch(() => null);
      } else {
        data = await response.text().catch(() => "");
      }
      if (!response.ok) {
        let detail = data && data.detail ? data.detail : data || `HTTP ${response.status}`;
        if (Array.isArray(detail)) {
          detail = detail.map((item) => item.msg || JSON.stringify(item)).join("; ");
        }
        if (typeof detail !== "string") detail = JSON.stringify(detail);
        throw new Error(detail);
      }
      return data;
    });
  }

  function toast(message, type = "info", title = "") {
    const stack = document.getElementById("toast-stack");
    if (!stack) return;
    const node = document.createElement("div");
    node.className = `toast ${type}`;
    node.innerHTML = `<span class="toast-icon"></span><div class="toast-body">${title ? `<strong>${escapeHtml(title)}</strong>` : ""}<span>${escapeHtml(message)}</span></div>`;
    stack.appendChild(node);
    window.setTimeout(() => {
      node.classList.add("closing");
      window.setTimeout(() => node.remove(), 220);
    }, 4600);
  }

  function applyLanguage() {
    const lang = state.lang === "ar" ? "ar" : "en";
    document.documentElement.lang = lang;
    document.documentElement.dir = lang === "ar" ? "rtl" : "ltr";
    try { localStorage.setItem("sentinel-lang", lang); } catch (error) { }
    $$("[data-i18n]").forEach((el) => {
      const key = el.getAttribute("data-i18n");
      if (key) el.textContent = t(key);
    });
    $$("[data-i18n-placeholder]").forEach((el) => {
      const key = el.getAttribute("data-i18n-placeholder");
      if (key) el.setAttribute("placeholder", t(key));
    });
    const langLabel = document.getElementById("lang-label");
    if (langLabel) langLabel.textContent = lang === "ar" ? "English" : "العربية";
    const page = document.body ? document.body.dataset.page : "";
    if (page && I18N.en[`page.${page}.title`]) {
      const brand = "SentinelAI";
      document.title = `${t(`page.${page}.title`)} | ${brand}`;
    }
    updateSoundButton();
    updateWsIndicator();
    document.dispatchEvent(new CustomEvent("app:language", { detail: { lang } }));
  }

  function setLanguage(lang) {
    state.lang = lang === "ar" ? "ar" : "en";
    applyLanguage();
  }

  function updateClock() {
    const node = document.getElementById("clock");
    if (!node) return;
    const locale = state.lang === "ar" ? "ar-SA" : "en-GB";
    node.textContent = new Intl.DateTimeFormat(locale, {
      hour: "2-digit", minute: "2-digit", second: "2-digit", hour12: false
    }).format(new Date());
  }

  function formatTime(value, withDate = true) {
    if (!value) return "";
    let date = new Date(value);
    if (Number.isNaN(date.getTime())) date = new Date(String(value).replace(" ", "T") + "Z");
    if (Number.isNaN(date.getTime())) return String(value);
    const locale = state.lang === "ar" ? "ar-SA" : "en-GB";
    const options = withDate
      ? { day: "2-digit", month: "short", hour: "2-digit", minute: "2-digit", hour12: false }
      : { hour: "2-digit", minute: "2-digit", second: "2-digit", hour12: false };
    return new Intl.DateTimeFormat(locale, options).format(date);
  }

  function timeAgo(value) {
    if (!value) return "";
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return "";
    const seconds = Math.max(0, Math.round((Date.now() - date.getTime()) / 1000));
    const locale = state.lang === "ar" ? "ar" : "en";
    const rtf = new Intl.RelativeTimeFormat(locale, { numeric: "auto" });
    if (seconds < 60) return rtf.format(-seconds, "second");
    const minutes = Math.round(seconds / 60);
    if (minutes < 60) return rtf.format(-minutes, "minute");
    const hours = Math.round(minutes / 60);
    if (hours < 24) return rtf.format(-hours, "hour");
    return rtf.format(-Math.round(hours / 24), "day");
  }

  function localizedDescription(event) {
    if (!event) return "";
    if (state.lang === "ar") return event.description_ar || event.description || "";
    return event.description || event.description_ar || "";
  }

  function severityClass(severity) {
    if (severity === "critical" || severity === "warning" || severity === "success" || severity === "info") return severity;
    return "info";
  }

  function kindIcon(kind) {
    if (kind === "threat" || kind === "risk_scan") return "i-shield";
    if (kind === "face_known" || kind === "face_unknown" || kind === "crowd") return "i-people";
    if (kind === "plate") return "i-cars";
    if (kind === "speech" || kind === "question" || kind === "inquiry") return "i-sound";
    if (kind === "gesture") return "i-agent";
    if (kind === "glasses") return "i-scan";
    return "i-camera";
  }

  function statusLabel(value, okText, badText) {
    return value ? (okText || t("dash.ready")) : (badText || t("dash.notReady"));
  }

  function ensureAudio() {
    if (!state.audioCtx) {
      const Ctor = window.AudioContext || window.webkitAudioContext;
      if (!Ctor) return null;
      try { state.audioCtx = new Ctor(); } catch (error) { return null; }
    }
    if (state.audioCtx.state === "suspended") {
      state.audioCtx.resume().catch(() => {});
    }
    return state.audioCtx;
  }

  function updateSoundButton() {
    const button = document.getElementById("sound-toggle");
    const icon = document.getElementById("sound-icon");
    const label = document.getElementById("sound-label");
    if (!button) return;
    button.classList.toggle("on", state.sound);
    if (icon) icon.innerHTML = `<use href="#${state.sound ? "i-sound" : "i-sound-off"}"></use>`;
    if (label) label.textContent = state.sound ? t("topbar.soundOn") : t("topbar.enableSound");
    document.dispatchEvent(new CustomEvent("app:sound", { detail: { enabled: state.sound } }));
  }

  function setSound(enabled, notify = true) {
    state.sound = Boolean(enabled);
    if (state.sound) {
      state.wantedSound = true;
      ensureAudio();
    }
    try { localStorage.setItem("sentinel-sound", state.sound ? "1" : "0"); } catch (error) { }
    if (!state.sound) stopSiren();
    updateSoundButton();
    if (notify) toast(t(state.sound ? "alarm.soundOn" : "alarm.soundOff"), state.sound ? "success" : "info");
  }

  function speak(text, language, force = false) {
    const value = String(text || "").trim();
    if (!value) return;
    if (!force && !state.sound) return;
    if (!("speechSynthesis" in window)) return;
    const now = Date.now();
    if (state.lastSpeech.text === value && now - state.lastSpeech.at < 6000) return;
    state.lastSpeech = { text: value, at: now };
    try {
      const utterance = new SpeechSynthesisUtterance(value.slice(0, 1200));
      const lang = language === "ar" ? "ar" : "en";
      utterance.lang = lang === "ar" ? "ar-SA" : "en-US";
      utterance.rate = 0.95;
      utterance.pitch = 1;
      const voices = window.speechSynthesis.getVoices();
      const match = voices.find((voice) => voice.lang && voice.lang.toLowerCase().startsWith(lang));
      if (match) utterance.voice = match;
      window.speechSynthesis.cancel();
      window.speechSynthesis.speak(utterance);
    } catch (error) { }
  }

  function sirenCycle() {
    if (!state.sound) return;
    const ctx = ensureAudio();
    if (!ctx) return;
    const start = ctx.currentTime;
    const oscillator = ctx.createOscillator();
    const gain = ctx.createGain();
    oscillator.type = "sawtooth";
    oscillator.frequency.setValueAtTime(920, start);
    oscillator.frequency.linearRampToValueAtTime(620, start + 0.42);
    oscillator.frequency.setValueAtTime(920, start + 0.46);
    oscillator.frequency.linearRampToValueAtTime(620, start + 0.88);
    gain.gain.setValueAtTime(0.0001, start);
    gain.gain.exponentialRampToValueAtTime(0.09, start + 0.04);
    gain.gain.setValueAtTime(0.09, start + 0.82);
    gain.gain.exponentialRampToValueAtTime(0.0001, start + 0.92);
    oscillator.connect(gain);
    gain.connect(ctx.destination);
    oscillator.start(start);
    oscillator.stop(start + 0.95);
  }

  function startSiren() {
    if (!state.sound) return;
    stopSiren();
    sirenCycle();
    state.sirenTimer = window.setInterval(sirenCycle, 1050);
    state.sirenStopTimer = window.setTimeout(stopSiren, 16000);
  }

  function stopSiren() {
    if (state.sirenTimer) {
      window.clearInterval(state.sirenTimer);
      state.sirenTimer = null;
    }
    if (state.sirenStopTimer) {
      window.clearTimeout(state.sirenStopTimer);
      state.sirenStopTimer = null;
    }
  }

  function showAlarm(event) {
    const overlay = document.getElementById("alarm-overlay");
    if (!overlay) return;
    if (state.lastAlarmId && !overlay.hidden && state.lastAlarmId === event.id) return;
    const meta = event.meta && typeof event.meta === "object" ? event.meta : {};
    const text = state.lang === "ar"
      ? (meta.alarm_ar || event.description_ar || event.description || "")
      : (meta.alarm_en || event.description || "");
    const title = document.getElementById("alarm-title");
    const body = document.getElementById("alarm-text");
    if (title) title.textContent = t("alarm.title");
    if (body) body.textContent = text || t("alarm.hint");
    overlay.hidden = false;
    state.lastAlarmId = event.id ?? null;
    if (state.sound) {
      startSiren();
      const speech = text || t("alarm.title");
      window.setTimeout(() => speak(speech, state.lang, true), 1900);
      ensureAudio();
    }
  }

  function dismissAlarm() {
    const overlay = document.getElementById("alarm-overlay");
    if (overlay) overlay.hidden = true;
    state.lastAlarmId = null;
    stopSiren();
    try { window.speechSynthesis.cancel(); } catch (error) { }
  }

  function handleEvent(event) {
    if (!event) return;
    const meta = event.meta && typeof event.meta === "object" ? event.meta : {};
    if (meta.sound_alarm) showAlarm(event);
    if (meta.speak_text && !meta.sound_alarm) {
      speak(meta.speak_text, meta.speak_language || "en", false);
    }
    state.listeners.forEach((listener) => {
      try { listener(event); } catch (error) { }
    });
  }

  function updateWsIndicator() {
    const dot = document.getElementById("ws-dot");
    const label = document.getElementById("ws-label");
    if (dot) dot.classList.toggle("offline", !state.wsConnected);
    if (label) {
      if (state.wsConnected) label.textContent = t("status.live");
      else if (state.ws) label.textContent = t("status.connecting");
      else label.textContent = t("status.offline");
    }
  }

  function connectWS() {
    if (!("WebSocket" in window)) {
      updateWsIndicator();
      return;
    }
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    let socket;
    try {
      socket = new WebSocket(`${protocol}//${window.location.host}/ws/alerts`);
    } catch (error) {
      scheduleReconnect();
      return;
    }
    state.ws = socket;
    updateWsIndicator();
    socket.addEventListener("open", () => {
      state.wsConnected = true;
      state.wsRetry = 1000;
      updateWsIndicator();
      if (state.pingTimer) window.clearInterval(state.pingTimer);
      state.pingTimer = window.setInterval(() => {
        if (socket.readyState === WebSocket.OPEN) socket.send("ping");
      }, 25000);
    });
    socket.addEventListener("message", (message) => {
      let payload;
      try { payload = JSON.parse(message.data); } catch (error) { return; }
      if (payload.type === "event" && payload.event) handleEvent(payload.event);
    });
    socket.addEventListener("close", () => {
      state.wsConnected = false;
      state.ws = null;
      if (state.pingTimer) {
        window.clearInterval(state.pingTimer);
        state.pingTimer = null;
      }
      updateWsIndicator();
      scheduleReconnect();
    });
    socket.addEventListener("error", () => {
      try { socket.close(); } catch (error) { }
    });
  }

  function scheduleReconnect() {
    if (state.wsTimer) return;
    const delay = state.wsRetry;
    state.wsRetry = Math.min(15000, Math.round(state.wsRetry * 1.7));
    state.wsTimer = window.setTimeout(() => {
      state.wsTimer = null;
      connectWS();
    }, delay);
  }

  function openModal({ title = "", subtitle = "", content = "", footer = "", wide = false }) {
    const root = document.getElementById("modal-root");
    if (!root) return { close() {}, root: null };
    root.innerHTML = `
      <div class="modal-backdrop" data-modal-backdrop>
        <div class="modal ${wide ? "wide" : ""}" role="dialog" aria-modal="true">
          <div class="modal-head">
            <div><h3>${escapeHtml(title)}</h3>${subtitle ? `<p>${escapeHtml(subtitle)}</p>` : ""}</div>
            <button type="button" class="icon-btn modal-x" aria-label="${escapeHtml(t("common.close"))}"><svg><use href="#i-close"></use></svg></button>
          </div>
          <div class="modal-body"></div>
          ${footer ? `<div class="modal-foot">${footer}</div>` : ""}
        </div>
      </div>`;
    const body = $(".modal-body", root);
    if (content instanceof Node) body.appendChild(content);
    else body.innerHTML = content;

    function close() {
      document.removeEventListener("keydown", onKey);
      root.innerHTML = "";
    }
    function onKey(event) {
      if (event.key === "Escape") close();
    }
    $("[data-modal-backdrop]", root).addEventListener("click", (event) => {
      if (event.target.matches("[data-modal-backdrop]")) close();
    });
    root.addEventListener("click", (event) => {
      if (event.target.closest(".modal-close, [data-modal-close], .modal-x")) {
        event.preventDefault();
        close();
      }
    });
    document.addEventListener("keydown", onKey);
    const input = $("input:not([type=hidden]):not([readonly]), textarea, select", body);
    if (input) window.setTimeout(() => input.focus(), 60);
    return { close, root };
  }

  function closeModal() {
    const root = document.getElementById("modal-root");
    if (root) root.innerHTML = "";
  }

  async function openEvent(eventId, onChanged) {
    const modal = openModal({
      title: t("detail.title"),
      subtitle: t("detail.loading"),
      content: `<div class="empty-inline">${escapeHtml(t("common.loading"))}</div>`,
      wide: true
    });
    let event;
    try {
      event = await api(`/api/events/${eventId}`);
    } catch (error) {
      modal.close();
      toast(error.message || t("events.loadFailed"), "error");
      return;
    }
    const meta = event.meta && typeof event.meta === "object" ? event.meta : {};
    const snapshot = safeUrl(event.snapshot_url);
    const clip = safeUrl(event.clip_url);
    const audio = safeUrl(event.audio_url);
    const description = localizedDescription(event);
    const translation = state.lang === "ar" ? event.description : event.description_ar;
    const metadataRows = [];
    if (meta.item) metadataRows.push([t("detail.item"), meta.item]);
    if (meta.plate) metadataRows.push([t("detail.plate"), meta.plate]);
    if (meta.gesture) metadataRows.push([t("detail.gesture"), meta.gesture]);
    if (meta.language) metadataRows.push([t("detail.language"), meta.language]);
    if (meta.provider || meta.answer_provider) metadataRows.push([t("detail.provider"), meta.provider || meta.answer_provider]);
    if (meta.confidence !== undefined) metadataRows.push([t("detail.confidence"), `${Math.round(Number(meta.confidence) * 100)}%`]);
    if (meta.registered !== undefined) metadataRows.push([t("detail.status"), meta.registered ? t("detail.registered") : t("detail.notRegistered")]);

    const findings = Array.isArray(meta.findings) ? meta.findings : [];
    const sources = Array.isArray(meta.sources) ? meta.sources : Array.isArray(meta.answer_sources) ? meta.answer_sources : [];
    const media = [];
    if (snapshot) media.push(`<div><div class="block-label">${escapeHtml(t("detail.snapshot"))}</div><img src="${escapeHtml(snapshot)}" alt=""></div>`);
    if (clip) media.push(`<div><div class="block-label">${escapeHtml(t("detail.video"))}</div><video controls preload="metadata" src="${escapeHtml(clip)}"></video></div>`);
    if (audio) media.push(`<div><div class="block-label">${escapeHtml(t("detail.audio"))}</div><audio class="audio-player" controls preload="metadata" src="${escapeHtml(audio)}"></audio></div>`);

    const content = `
      <div class="detail-grid">
        <div class="kv"><span>${escapeHtml(t("detail.kind"))}</span><strong>${escapeHtml(t(`kind.${event.kind}`) === `kind.${event.kind}` ? event.kind : t(`kind.${event.kind}`))}</strong></div>
        <div class="kv"><span>${escapeHtml(t("detail.severity"))}</span><strong><span class="badge ${severityClass(event.severity)}">${escapeHtml(t(`severity.${event.severity}`))}</span></strong></div>
        <div class="kv"><span>${escapeHtml(t("detail.person"))}</span><strong>${escapeHtml(event.person_name || t("common.unknown"))}</strong></div>
        <div class="kv"><span>${escapeHtml(t("detail.time"))}</span><strong>${escapeHtml(formatTime(event.created_at))}</strong></div>
        <div class="kv"><span>${escapeHtml(t("detail.status"))}</span><strong>${escapeHtml(event.acknowledged ? t("detail.acknowledged") : t("detail.pending"))}</strong></div>
      </div>
      ${media.length ? `<div class="detail-media">${media.join("")}</div>` : `<div class="mini-note">${escapeHtml(t("detail.noEvidence"))}</div>`}
      <div class="block-label">${escapeHtml(t("detail.description"))}</div>
      <div class="translation-block">${escapeHtml(description || event.title)}</div>
      ${translation ? `<div class="block-label">${escapeHtml(state.lang === "ar" ? t("detail.englishOriginal") : t("detail.arabicTranslation"))}</div><div class="translation-block ${state.lang === "ar" ? "" : "ar"}">${escapeHtml(translation)}</div>` : ""}
      ${event.transcript ? `<div class="block-label">${escapeHtml(t("detail.transcript"))}</div><div class="translation-block mono">${escapeHtml(event.transcript)}</div>` : ""}
      ${event.translation ? `<div class="block-label">${escapeHtml(t("detail.translation"))}</div><div class="translation-block">${escapeHtml(event.translation)}</div>` : ""}
      ${findings.length ? `<div class="block-label">${escapeHtml(t("detail.riskFindings"))}</div><div class="risk-findings">${findings.map((finding) => `<span class="badge ${severityClass(finding.severity)}">${escapeHtml(finding.label)} ${finding.confidence !== undefined ? Math.round(Number(finding.confidence) * 100) + "%" : ""}</span>`).join("")}</div>` : ""}
      ${sources.length ? `<div class="block-label">${escapeHtml(t("detail.sources"))}</div><div class="source-list">${sources.map((source) => `<span>${escapeHtml(source.title || source.source || source)}</span>`).join("")}</div>` : ""}
      ${metadataRows.length ? `<div class="block-label">${escapeHtml(t("detail.metadata"))}</div><div class="detail-grid">${metadataRows.map(([key, value]) => `<div class="kv"><span>${escapeHtml(key)}</span><strong>${escapeHtml(value)}</strong></div>`).join("")}</div>` : ""}
    `;

    const current = openModal({
      title: event.title,
      subtitle: `${t(`kind.${event.kind}`)} · ${formatTime(event.created_at)}`,
      content,
      wide: true,
      footer: `${event.acknowledged ? "" : `<button type="button" class="btn btn-primary" id="event-ack">${escapeHtml(t("common.acknowledge"))}</button>`}<button type="button" class="btn btn-danger" id="event-delete">${escapeHtml(t("common.delete"))}</button><button type="button" class="btn btn-ghost modal-close">${escapeHtml(t("common.close"))}</button>`
    });
    modal.close();

    const ackButton = current.root && current.root.querySelector("#event-ack");
    if (ackButton) {
      ackButton.addEventListener("click", async () => {
        try {
          await api(`/api/events/${event.id}/ack`, { method: "POST" });
          toast(t("detail.acknowledgedToast"), "success");
          current.close();
          if (onChanged) onChanged();
        } catch (error) {
          toast(error.message || t("detail.actionFailed"), "error");
        }
      });
    }
    const deleteButton = current.root && current.root.querySelector("#event-delete");
    if (deleteButton) {
      deleteButton.addEventListener("click", async () => {
        if (!window.confirm(t("detail.deleteConfirm"))) return;
        try {
          await api(`/api/events/${event.id}`, { method: "DELETE" });
          toast(t("detail.deleted"), "success");
          current.close();
          if (onChanged) onChanged();
        } catch (error) {
          toast(error.message || t("detail.actionFailed"), "error");
        }
      });
    }
  }

  function initTopbar() {
    const langToggle = document.getElementById("lang-toggle");
    if (langToggle) {
      langToggle.addEventListener("click", () => setLanguage(state.lang === "ar" ? "en" : "ar"));
    }
    const soundToggle = document.getElementById("sound-toggle");
    if (soundToggle) {
      soundToggle.addEventListener("click", () => {
        ensureAudio();
        setSound(!state.sound);
      });
    }
    const dismiss = document.getElementById("alarm-dismiss");
    if (dismiss) dismiss.addEventListener("click", dismissAlarm);
    const menu = document.getElementById("menu-btn");
    const sidebar = document.getElementById("sidebar");
    if (menu && sidebar) {
      menu.addEventListener("click", (event) => {
        event.stopPropagation();
        sidebar.classList.toggle("open");
      });
      document.addEventListener("click", (event) => {
        if (!sidebar.contains(event.target) && !menu.contains(event.target)) sidebar.classList.remove("open");
      });
      $$(".nav-item", sidebar).forEach((link) => link.addEventListener("click", () => sidebar.classList.remove("open")));
    }
  }

  function init() {
    try {
      const stored = localStorage.getItem("sentinel-lang");
      state.lang = stored === "ar" ? "ar" : "en";
    } catch (error) {
      state.lang = document.documentElement.lang === "ar" ? "ar" : "en";
    }
    try {
      state.wantedSound = localStorage.getItem("sentinel-sound") === "1";
    } catch (error) {
      state.wantedSound = false;
    }
    state.sound = false;
    initTopbar();
    applyLanguage();
    updateClock();
    window.setInterval(updateClock, 1000);
    connectWS();
    document.addEventListener("pointerdown", function unlock() {
      if (state.wantedSound && !state.sound) {
        state.sound = true;
        ensureAudio();
        updateSoundButton();
      }
    }, { once: true });
    window.addEventListener("beforeunload", () => {
      stopSiren();
      if (state.pingTimer) window.clearInterval(state.pingTimer);
      if (state.ws) state.ws.close();
    });
  }

  window.App = {
    t,
    api,
    toast,
    modal: openModal,
    closeModal,
    openEvent,
    onEvent(listener) {
      state.listeners.add(listener);
      return () => state.listeners.delete(listener);
    },
    get lang() { return state.lang; },
    get soundEnabled() { return state.sound; },
    setLanguage,
    translate: t,
    escapeHtml,
    safeUrl,
    formatTime,
    timeAgo,
    severityClass,
    kindIcon,
    localizedDescription,
    speak,
    dismissAlarm,
    setSound
  };

  init();
})();
