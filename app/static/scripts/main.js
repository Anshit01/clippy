document.getElementById('textarea').innerHTML = "Helloafsdf"
var curTime = getCurrentTime()
var lastUpdateTime = getPreciseCurrentTime()
var textareaText = ''
var connection_id = ''

// Firebase configuration
var firebaseConfig = {
    apiKey: "AIzaSyBlkHqdolHzPDu7lYuAmPv7K1ImaPAr9Lk",
    authDomain: "clippy-3da02.firebaseapp.com",
    databaseURL: "https://clippy-3da02.firebaseio.com",
    projectId: "clippy-3da02",
    storageBucket: "clippy-3da02.appspot.com",
    messagingSenderId: "476084889049",
    appId: "1:476084889049:web:84211cd1769b7ef39225c8"
  };
// Initialize Firebase
firebase.initializeApp(firebaseConfig);

var provider = new firebase.auth.GoogleAuthProvider();



$(document).ready( () => {

    $('#login-btn').click(() => {
        alert('asf')
    })

    var socket = io.connect('/')
    socket.on('connect', () => {
        socket.send('User has connected!')
    })

    socket.on('connect_response', (con_id) => {
        connection_id = con_id
        console.log('connected with connection_id: ' + connection_id)
    })

    socket.on('message', (msg) => {
        console.log('message: ' + msg)
    })

    socket.on('text_response', (con_id, text, timestamp) => {
        if(connection_id != con_id && timestamp > lastUpdateTime){
            textareaText = text
            $('#textarea').val(text)
        }
    })

    $('#btn1').click(() => {
        // socket.send('asfjafkdahfkh')
    })

    // $('#textarea').on('input', () => {
    //     text = $('#textarea').val()
    //     socket.send(text)
    // })
    
    setInterval(() => {
        var curText = $('#textarea').val()
        if(curText != textareaText){
            socket.emit('update_text', connection_id, curText, getPreciseCurrentTime())
            textareaText = curText
        }
    }, 1000)

})

function getCurrentTime() {
    return Math.floor(new Date().getTime() / 1000)
}

function getPreciseCurrentTime() {
    return new Date().getTime()
}