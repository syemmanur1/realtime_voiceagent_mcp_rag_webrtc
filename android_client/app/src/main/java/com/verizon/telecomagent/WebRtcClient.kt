package com.example.telecomagent // Change to your package name

import android.content.Context
import org.webrtc.*
import org.webrtc.audio.AudioDeviceModule
import org.webrtc.audio.JavaAudioDeviceModule

class WebRtcClient(
    context: Context,
    private val observer: PeerConnection.Observer
) {

    private val peerConnectionFactory: PeerConnectionFactory
    private var peerConnection: PeerConnection? = null
    private val audioSource: AudioSource
    private val localAudioTrack: AudioTrack

    init {
        // Initialize PeerConnectionFactory
        PeerConnectionFactory.initialize(
            PeerConnectionFactory.InitializationOptions.builder(context)
                .setEnableInternalTracer(true)
                .createInitializationOptions()
        )
        val options = PeerConnectionFactory.Options()
        val adm: AudioDeviceModule = JavaAudioDeviceModule.builder(context).createAudioDeviceModule()
        peerConnectionFactory = PeerConnectionFactory.builder()
            .setOptions(options)
            .setAudioDeviceModule(adm)
            .createPeerConnectionFactory()
        adm.release()

        // Create audio source and track
        audioSource = peerConnectionFactory.createAudioSource(MediaConstraints())
        localAudioTrack = peerConnectionFactory.createAudioTrack("local_audio_track", audioSource)
    }

    fun createPeerConnection() {
        val rtcConfig = PeerConnection.RTCConfiguration(emptyList())
        peerConnection = peerConnectionFactory.createPeerConnection(rtcConfig, observer)
        peerConnection?.addTrack(localAudioTrack)
    }

    fun createOffer(sdpObserver: SdpObserver) {
        val mediaConstraints = MediaConstraints().apply {
            mandatory.add(MediaConstraints.KeyValuePair("OfferToReceiveAudio", "true"))
        }
        peerConnection?.createOffer(sdpObserver, mediaConstraints)
    }

    fun setRemoteDescription(sessionDescription: SessionDescription, sdpObserver: SdpObserver) {
        peerConnection?.setRemoteDescription(sdpObserver, sessionDescription)
    }

    fun setLocalDescription(sessionDescription: SessionDescription, sdpObserver: SdpObserver) {
        peerConnection?.setLocalDescription(sdpObserver, sessionDescription)
    }
    
    fun close() {
        peerConnection?.close()
        peerConnection = null
    }
}

// Simple SdpObserver implementation
open class SimpleSdpObserver : SdpObserver {
    override fun onCreateSuccess(p0: SessionDescription?) {}
    override fun onSetSuccess() {}
    override fun onCreateFailure(p0: String?) {}
    override fun onSetFailure(p0: String?) {}
}
