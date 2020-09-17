// document.getElementById('textarea').innerHTML = "Helloafsdf"
var curTime = getCurrentTime()
var lastUpdateTime = getPreciseCurrentTime()
var textareaText = ''

var connectionId = ''
var userId = ''
var user_name = ''
var user_email = ''
var photoURL = ''

var clipId = ''
var clipName = 'Untitled'

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

var socket
$(document).ready( () => {

    var textareaTopOffset = $('#textarea').offset().top
    $('#textarea').outerHeight($(document).height() - textareaTopOffset)

    $('#textarea').focus();

    $(window).on('resize', () => {
        $('#textarea').outerHeight($(document).height() - $('#textarea').offset().top)
    })

    $('#new-btn').click(() => {
        var clipsArray = []
        $('.recent-clip').each(function() {
            clipsArray.push($(this).html())
        })
        var newClipName = 'Untitled'
        if(clipsArray.indexOf(newClipName) != -1){
            var ind = 1
            while(clipsArray.indexOf(newClipName + '-' + ind) != -1){
                ind++
            }
            newClipName += '-' + ind
        }
        socket.emit('new_clip', userId, newClipName)
    })

    

    $('#login-btn').click(() => {
        if($('#login-btn').html() == 'Login'){
            firebase.auth().signInWithPopup(provider).then(function(result) {
                var name = result.user.displayName
                var email = result.user.email
                var uid = result.user.uid
                photoURL = result.user.photoURL
                socket.emit('login', name, email, uid, photoURL)
                console.log('logged in')
            }).catch(function(error) {
                // Handle Errors here.
                var errorCode = error.code;
                var errorMessage = error.message;
                // The email of the user's account used.
                var email = error.email;
                // The firebase.auth.AuthCredential type that was used.
                var credential = error.credential;
                console.log('error in login')
            });
        }else{
            socket.emit('logout')
            firebase.auth().signOut().then(function() {
                console.log('Signed out')
                $('#login-btn').html('Login')
                $('#profile-img').attr('src', '/static/styles/images/user.png')
            }).catch(function(error) {
                console.error('Sign out error')
            });
        }
    })

    socket = io.connect('/')
    socket.on('connect', () => {
        socket.send('User has connected!')
    })

    socket.on('connect_response', (con_id) => {
        connectionId = con_id
        console.log('connected with connectionId: ' + connectionId)
    })

    socket.on('login_response', (err, id, name, email, clipList, recentClipId, photo_URL) => {
        console.log('logged in finally')
        if(err){
            console.error('error in login to backend')
            console.error(err)
        }else{
            userId = id
            userName = name
            userEmail = email
            photoURL = photo_URL
            $('#profile-img').attr('src', photoURL)
            $('#login-btn').html('Log out')
            
            //filling recent clips drop down list
            var clipLength = Object.keys(clipList).length
            var i = 1
            var content = ''
            for(clip_id in clipList){
                content += '<a id="' + clip_id + '" class="dropdown-item recent-clip">' + clipList[clip_id] + '</a>'
                if(i < clipLength){
                    content += '<div class="dropdown-divider"></div>'
                }
                i++
            }
            $('#recent-clip-list').html(content)

            socket.emit('get_clip', userId, recentClipId)
        }
    })

    socket.on('message', (msg) => {
        console.log('message: ' + msg)
    })

    socket.on('test_response', (err, json) => {
        console.log(err);
        console.log(json)
    })

    socket.on('text_response', (con_id, text, timestamp) => {
        if(connectionId != con_id && timestamp > lastUpdateTime){
            textareaText = text
            $('#textarea').val(text)
        }
    })

    socket.on('clip_response', (err, clip_id, clip_name, clipData) => {
        if(err){
            console.error(err)
        }else{
            clipName = clip_name
            clipId = clip_id
            $('#clip-name').val(clipName)
            if(clipData){
                $('#textarea').val(clipData)
            }
        }
    })

    socket.on('new_clip_response', (err, newClipId, newClipName) => {
        if(err){
            console.error(err)
        }else{
            clipId = newClipId
            clipName = newClipName
            $('#clip-name').val(clipName)
            $('#textarea').val('')
            $('#recent-clip-list').html(
                '<a id="' + clipId + '" class="dropdown-item recent-clip">' + clipName + '</a>'
                + '<div class="dropdown-divider"></div>'
                + $('#recent-clip-list').html()
            )
        }
    })

    socket.on('logout_response', (err, res) => {
        if(err){
            console.error(err)
        }else{
            console.log(res)
        }
    })

    // $('#textarea').on('input', () => {
    //     text = $('#textarea').val()
    //     socket.send(text)
    // })
    
    setInterval(() => {
        var curText = $('#textarea').val()
        var curName = $('#clip-name').val()
        if(curText != textareaText || curName != clipName) {
            socket.emit('update_text', connectionId, userId, clipId, curName, curText, getPreciseCurrentTime())
            textareaText = curText
            clipName = curName
        }
    }, 1000)

})

function getCurrentTime() {
    return Math.floor(new Date().getTime() / 1000)
}

function getPreciseCurrentTime() {
    return new Date().getTime()
}