package com.example.telecomagent // Change to your package name

import android.Manifest
import android.content.pm.PackageManager
import androidx.appcompat.app.AppCompatActivity
import android.os.Bundle
import android.widget.Toast
import androidx.core.app.ActivityCompat
import androidx.core.content.ContextCompat
import com.example.telecomagent.databinding.ActivityMainBinding
import org.webrtc.*

class MainActivity : AppCompatActivity() {

    private lateinit var binding: ActivityMainBinding
    private lateinit var webRtcClient: WebRtcClient
    private lateinit var signalingClient: SignalingClient

    // IMPORTANT: Change this to your Replit WebSocket URL
    private val serverUrl = "wss://your-repl-name.replit.dev/ws"

    private val AUDIO_PERMISSION_REQUEST_CODE = 1

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityMainBinding.inflate(layoutInflater)
        setContentView(binding.root)

        checkPermissions()
    }

    private fun checkPermissions() {
        if (ContextCompat.checkSelfPermission(this, Manifest.permission.RECORD_AUDIO) != PackageManager.PERMISSION_GRANTED) {
            ActivityCompat.requestPermissions(this, arrayOf(Manifest.permission.RECORD_AUDIO), AUDIO_PERMISSION_REQUEST_CODE)
        } else {
            initialize()
        }
    }

    override fun onRequestPermissionsResult(requestCode: Int, permissions: Array<out String>, grantResults: IntArray) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults)
        if (requestCode == AUDIO_PERMISSION_REQUEST_CODE && grantResults.isNotEmpty() && grantResults[0] == PackageManager.PERMISSION_GRANTED) {
            initialize()
        } else {
            Toast.makeText(this, "Microphone permission is required.", Toast.LENGTH_LONG).show()
            binding.startButton.isEnabled = false
        }
    }

    private fun initialize() {
        binding.startButton.setOnClickListener {
            startSession()
        }
    }

    private fun startSession() {
        if (serverUrl.contains("your-repl-name")) {
            Toast.makeText(this, "Error: Please set the server URL in MainActivity.kt", Toast.LENGTH_LONG).show()
            return
        }
        
        binding.startButton.isEnabled = false
        updateStatus("Connecting...")

        // Setup WebRTC Client
        webRtcClient = WebRtcClient(applicationContext, object : PeerConnection.Observer {
            override fun onIceCandidate(candidate: IceCandidate?) {
                // Not needed for bot communication, but can be implemented
            }
            override fun onDataChannel(p0: DataChannel?) {}
            override fun onIceConnectionReceivingChange(p0: Boolean) {}
            override fun onIceConnectionChange(p0: PeerConnection.IceConnectionState?) {}
            override fun onIceGatheringChange(p0: PeerConnection.IceGatheringState?) {}
            override fun onSignalingChange(p0: PeerConnection.SignalingState?) {}
            override fun onAddStream(p0: MediaStream?) {}
            override fun onRemoveStream(p0: MediaStream?) {}
            override fun onRenegotiationNeeded() {}
            override fun onAddTrack(p0: RtpReceiver?, p1: Array<out MediaStream>?) {}
        })

        // Setup Signaling Client
        signalingClient = SignalingClient(serverUrl, createSignalingListener())
        signalingClient.connect()
    }

    private fun createSignalingListener() = object : SignalingListener {
        override fun onConnectionEstablished() {
            runOnUiThread {
                updateStatus("Creating Offer...")
                webRtcClient.createPeerConnection()
                webRtcClient.createOffer(object : SimpleSdpObserver() {
                    override fun onCreateSuccess(sessionDescription: SessionDescription?) {
                        sessionDescription?.let {
                            webRtcClient.setLocalDescription(it, object : SimpleSdpObserver() {
                                override fun onSetSuccess() {
                                    val offer = mapOf("sdp" to it.description, "type" to it.type.canonicalForm())
                                    signalingClient.send(offer)
                                }
                            })
                        }
                    }
                })
            }
        }

        override fun onAnswerReceived(description: SessionDescription) {
            runOnUiThread {
                updateStatus("Listening...")
                webRtcClient.setRemoteDescription(description, object : SimpleSdpObserver())
            }
        }
        
        // Unused for this implementation
        override fun onOfferReceived(description: SessionDescription) {}
        override fun onIceCandidateReceived(iceCandidate: IceCandidate) {}
        override fun onConnectionClosed() {
            runOnUiThread {
                updateStatus("Disconnected")
                binding.startButton.isEnabled = true
                webRtcClient.close()
            }
        }
    }

    private fun updateStatus(status: String) {
        binding.statusTextView.text = status
    }

    override fun onDestroy() {
        signalingClient.close()
        super.onDestroy()
    }
}
