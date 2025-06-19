package com.example.telecomagent // Change to your package name

import com.google.gson.Gson
import okhttp3.*
import org.webrtc.IceCandidate
import org.webrtc.SessionDescription

// Listener for signaling events
interface SignalingListener {
    fun onConnectionEstablished()
    fun onOfferReceived(description: SessionDescription)
    fun onAnswerReceived(description: SessionDescription)
    fun onIceCandidateReceived(iceCandidate: IceCandidate)
    fun onConnectionClosed()
}

class SignalingClient(private val serverUrl: String, private val listener: SignalingListener) {

    private var webSocket: WebSocket? = null
    private val gson = Gson()

    fun connect() {
        val client = OkHttpClient()
        val request = Request.Builder().url(serverUrl).build()
        webSocket = client.newWebSocket(request, object : WebSocketListener() {
            override fun onOpen(webSocket: WebSocket, response: Response) {
                listener.onConnectionEstablished()
            }

            override fun onMessage(webSocket: WebSocket, text: String) {
                val message = gson.fromJson(text, Map::class.java)
                when (message["type"]) {
                    "answer" -> {
                        val sdp = message["sdp"] as String
                        listener.onAnswerReceived(SessionDescription(SessionDescription.Type.ANSWER, sdp))
                    }
                    "ice-candidate" -> {
                        // This part is for client-to-client, not needed for bot, but good practice
                    }
                }
            }

            override fun onClosing(webSocket: WebSocket, code: Int, reason: String) {
                listener.onConnectionClosed()
            }

            override fun onFailure(webSocket: WebSocket, t: Throwable, response: Response?) {
                listener.onConnectionClosed()
            }
        })
    }

    fun send(message: Map<String, Any>) {
        webSocket?.send(gson.toJson(message))
    }

    fun close() {
        webSocket?.close(1000, "Client closed.")
    }
}
