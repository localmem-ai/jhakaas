# Product Requirements Document (PRD): Jhakaas

## 1. Executive Summary
**Jhakaas** is a social photo enhancement platform designed for Indian friend groups. It transforms the chaotic process of sharing event photos into a collaborative, gamified experience. By combining centralized event albums, AI-powered enhancements (style transfer, face fix), and a democratic voting system, Jhakaas ensures that only the best, most "Instagram-worthy" moments are curated and shared.

## 2. Problem Statement
- **Fragmentation**: Photos from weddings, trips, and parties are scattered across WhatsApp, Google Drive, and local storages.
- **Quality vs. Quantity**: Groups take hundreds of photos, but few are edited or posted because the effort is too high.
- **Social Friction**: Deciding which group photo to post involves back-and-forth messaging ("Send me the one where I look good").
- **Lack of Cultural Context**: Generic editors lack styles that resonate with Indian festivities and aesthetics.

## 3. Target Audience
### Primary Persona: "The Social Squad Leader"
- **Demographics**: 20-28 years old, Metro cities (Mumbai, Delhi, Bangalore).
- **Behavior**: Organizes plans, takes the most photos, seeks social validation (likes/comments).
- **Motivation**: Wants the group's memories to look premium and cohesive without spending hours editing.

## 4. Core Features & Functional Requirements

### 4.1 Event-Based Albums (The Container)
- **Create Event**: Users can create an event (e.g., "Rohan's Wedding", "Goa Trip") with a date and location.
- **Invite System**: Shareable links/codes (WhatsApp integration) for easy onboarding.
- **Collaborative Upload**: All participants can upload raw photos (high-res preservation).
- **Privacy**: Options for Public (link-accessible) or Private (invite-only) events.

### 4.2 AI Photo Enhancement (The Magic)
- **Style Transfer**: Artistic filters (Oil painting, Sketch) and culturally relevant themes ("Monsoon", "Haldi Ceremony", "Bollywood Poster").
- **Face Enhancement**: "Beauty mode" for groups—ensuring everyone looks good (skin smoothing, lighting fix).
- **Background Magic**: Blur background (Bokeh), sky replacement, or object removal (magic eraser).
- **Performance**: Processing time target < 30s per photo.

### 4.3 Collaborative Curation (The Game)
- **Voting System**: "Tinder for your photos". Users upvote their favorite enhanced versions.
- **Leaderboard**: Real-time ranking of photos.
- **Winner Selection**: Top-voted photos are automatically curated into a "Best of" gallery.

### 4.4 Social Sharing (The Output)
- **One-Tap Share**: Direct integration with Instagram Stories/Feed and WhatsApp Status.
- **Smart Cropping**: Auto-crop to 9:16 (Story) or 4:5 (Feed) without losing key subjects.
- **Watermark**: "Enhanced by Jhakaas" watermark (removable via Premium).

## 5. User Journey: "The Weekend Trip"
1.  **Friday**: Rohan creates "Lonavala Weekend" event on Jhakaas and shares the link on the WhatsApp group.
2.  **Saturday**: Friends upload 150+ raw photos to the event throughout the day.
3.  **Sunday Morning**: Priya uses Jhakaas AI to apply a "Moody Monsoon" style to a group trek photo.
4.  **Sunday Afternoon**: The group gets a notification. Everyone votes. Priya's version gets 8 upvotes.
5.  **Sunday Evening**: The photo is marked a "Winner". Rohan shares it directly to his Instagram Story with one click.

## 6. Monetization Strategy (Freemium)
- **Free Tier**: Unlimited uploads, basic filters, voting, watermarked AI exports.
- **Premium (Jhakaas Gold)**:
    - High-res downloads (Print quality).
    - Advanced/Exclusive AI styles.
    - No watermarks.
    - Priority processing.
    - "Group Pool" payment option (split the cost).

## 7. Technical Constraints & Requirements
- **Platform**: Web-first (PWA) for low friction, followed by Mobile Apps (iOS/Android).
- **AI Processing**: Asynchronous processing to prevent UI blocking.
- **Storage**: Scalable cloud storage (S3/Cloudinary) with auto-archiving policies for old events.

## 8. Success Metrics
- **North Star**: Number of "Winner" photos shared to social media per event.
- **Engagement**: Average votes per photo.
- **Retention**: % of users who join a second event within 30 days.
