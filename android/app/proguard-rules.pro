# Moshi reflective adapters
-keep class kotlin.Metadata { *; }
-keepclassmembers class ** {
    @com.squareup.moshi.FromJson <methods>;
    @com.squareup.moshi.ToJson <methods>;
}
# Retrofit
-keepattributes Signature, InnerClasses, EnclosingMethod
-keep,allowobfuscation interface retrofit2.Call
